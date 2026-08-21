
"""ideaToProd MCP orchestrator.

This server imports agents from separate local modules and orchestrates a 5-step
pipeline that creates a project folder, generates designs, writes code and tests,
and executes the resulting unit tests.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable

from agent1_hl_design import create_hl_design
from agent2_detailed_design import create_detailed_design
from agent3_code_generation import generate_code
from agent4_unit_test_generation import generate_unit_tests
from agent5_test_execution import execute_tests
from agent6_deployment import package_application


PROJECT_SUBFOLDERS = ["docs", "code", "tests", "results"]


def safe_project_name(idea_name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9 _-]", "", idea_name).strip()
    sanitized = re.sub(r"[ \t]+", " ", sanitized)
    if not sanitized:
        return "GeneratedProject"
    return sanitized.replace(" ", "_")


def create_project_structure(base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    for folder_name in PROJECT_SUBFOLDERS:
        (base_dir / folder_name).mkdir(exist_ok=True)


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def remove_file_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def verify_high_level_design(idea_name: str, idea_description: str, output: str) -> bool:
    if not output.strip():
        return False
    return idea_name in output or idea_description.split()[0] in output


def verify_detailed_design(output: str) -> bool:
    return bool(output.strip()) and "Detailed design" in output


def verify_code(output: str) -> bool:
    if not output.strip():
        return False

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return "def get_application_summary" in output and "def run_application" in output

    if not isinstance(data, dict):
        return False

    files = data.get("files")
    summary = data.get("summary")
    if not isinstance(files, list) or not isinstance(summary, str):
        return False

    return bool(files)


def parse_generated_code_output(output: str) -> list[dict] | None:
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    files = data.get("files")
    if not isinstance(files, list):
        return None

    valid_files: list[dict] = []
    for file_item in files:
        if (
            isinstance(file_item, dict)
            and isinstance(file_item.get("path"), str)
            and isinstance(file_item.get("content"), str)
        ):
            valid_files.append(file_item)

    return valid_files if valid_files else None


def verify_tests(output: str) -> bool:
    return "def test_summary_not_empty" in output and "def test_run_application_returns_none" in output


def get_clarification_prompts(stage_name: str) -> list[str]:
    prompts = {
        "high-level design": [
            "Clarify the main user personas and what they need from the system.",
            "Clarify the primary product goals and success criteria.",
            "Clarify any constraints or assumptions you want the design to honor.",
        ],
        "detailed design": [
            "Clarify the desired module structure or component boundaries.",
            "Clarify any important performance, error handling, or validation requirements.",
            "Clarify what should be easy to test or validate in the resulting design.",
        ],
        "code generation": [
            "Clarify any specific implementation details, APIs, or behaviors that must be present.",
            "Clarify how edge cases and invalid inputs should be handled.",
            "Clarify what the expected application entry point and observable outputs should be.",
        ],
        "unit test generation": [
            "Clarify which code paths and functions are most important to verify.",
            "Clarify any edge cases or failure modes that must be covered.",
            "Clarify what regression risk should be protected by a dedicated regression test.",
        ],
    }
    return prompts.get(stage_name, [
        "Clarify the missing or uncertain requirements for this stage.",
        "Clarify any acceptance criteria or expected behavior.",
    ])


def write_generated_files(base_dir: Path, generated_files: list[dict]) -> None:
    for file_item in generated_files:
        file_path = base_dir / file_item["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        write_text_file(file_path, file_item["content"])


def dump_code_dir(code_dir: Path) -> str:
    sections: list[str] = []
    for path in sorted(code_dir.rglob("*.py")):
        if path.is_file():
            relative_path = path.relative_to(code_dir).as_posix()
            sections.append(f"# path: {relative_path}\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(sections)


def extract_open_questions(hl_design: str) -> list[str]:
    lines = hl_design.splitlines()
    questions: list[str] = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            in_section = re.sub(r"^#+\s*", "", stripped).strip().lower() == "open questions"
            continue
        if not in_section or not stripped:
            continue
        question = re.sub(r"^[-*]\s+|^\d+[.)]\s+", "", stripped).strip()
        if question:
            questions.append(question)

    return questions


def request_clarification(stage_name: str, extra_prompts: list[str] | None = None) -> str | None:
    prompts = get_clarification_prompts(stage_name) + (extra_prompts or [])
    answers: list[str] = []

    print(f"\nClarification required for {stage_name}. Answer each prompt or press Enter to accept it.")
    for prompt in prompts:
        print(f"\n- {prompt}")
        answer = input("Provide guidance, or press Enter to accept this item: ").strip()
        if answer:
            answers.append(f"{prompt}\n{answer}")

    if not answers:
        print("All clarification prompts were accepted as-is.")
        return None

    return "\n\n".join(answers)


def run_agent_with_verification(
    stage_name: str,
    action: Callable[..., str],
    validator: Callable[[str], bool],
    *args,
    extra_prompts: list[str] | None = None,
) -> tuple[str, str | None]:
    output = action(*args)
    if validator(output):
        return output, None

    report_progress(f"{stage_name}: output needs clarification, requesting input...")
    clarification = request_clarification(stage_name, extra_prompts=extra_prompts)
    if clarification is None:
        return output, None

    output = action(*args, clarification=clarification)
    return output, clarification


def report_progress(message: str) -> None:
    print(f"[ideaToProd] {message}", flush=True)


def orchestrate(idea_name: str, idea_description: str) -> str:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent / "Projects" / safe_project_name(idea_name)
    create_project_structure(project_root)

    docs_dir = project_root / "docs"
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    results_dir = project_root / "results"

    report_progress(f"Project folder ready at {project_root}")

    report_progress("Step 1/5: Generating high-level design...")
    hl_design, hl_clarification = run_agent_with_verification(
        "high-level design",
        create_hl_design,
        lambda output: verify_high_level_design(idea_name, idea_description, output),
        idea_name,
        idea_description,
    )
    remove_file_if_exists(docs_dir / "high_level_design.txt")
    write_text_file(docs_dir / "high_level_design.md", hl_design)
    report_progress("Step 1/5: High-level design complete.")

    report_progress("Step 2/5: Generating detailed design...")
    open_questions = extract_open_questions(hl_design)
    detailed_design, detailed_clarification = run_agent_with_verification(
        "detailed design",
        create_detailed_design,
        verify_detailed_design,
        hl_design,
        extra_prompts=open_questions,
    )
    remove_file_if_exists(docs_dir / "detailed_design.txt")
    write_text_file(docs_dir / "detailed_design.md", detailed_design)
    report_progress("Step 2/5: Detailed design complete.")

    report_progress("Step 3/5: Generating application code...")
    code_text, code_clarification = run_agent_with_verification(
        "code generation",
        generate_code,
        verify_code,
        detailed_design,
    )

    generated_files = parse_generated_code_output(code_text)
    if generated_files is not None:
        write_generated_files(code_dir, generated_files)
    else:
        write_text_file(code_dir / "app.py", code_text)
    report_progress("Step 3/5: Code generation complete.")

    report_progress("Step 4/5: Generating unit tests...")
    tests_text, tests_clarification = run_agent_with_verification(
        "unit test generation",
        generate_unit_tests,
        verify_tests,
        code_dir,
        tests_dir,
    )
    generated_test_files = parse_generated_code_output(tests_text)
    if generated_test_files is not None:
        write_generated_files(tests_dir, generated_test_files)
        if not (tests_dir / "__init__.py").exists():
            write_text_file(tests_dir / "__init__.py", "# Test package for generated code.\n")
    else:
        if not (tests_dir / "__init__.py").exists():
            write_text_file(tests_dir / "__init__.py", "# Test package for generated code.\n")
        write_text_file(tests_dir / "test_app.py", tests_text)
    report_progress("Step 4/5: Unit test generation complete.")

    max_fix_attempts = 3
    fix_attempts = 0
    report_progress("Step 5/5: Executing tests...")
    test_results, tests_passed = execute_tests(project_root)
    write_text_file(results_dir / "test_results.txt", test_results)
    report_progress(f"Step 5/5: Test run complete - {'PASSED' if tests_passed else 'FAILED'}.")

    while not tests_passed and fix_attempts < max_fix_attempts:
        fix_attempts += 1
        report_progress(
            f"Tests failed. Starting fix attempt {fix_attempts}/{max_fix_attempts}..."
        )
        existing_code = dump_code_dir(code_dir)
        fixed_code_text = generate_code(
            detailed_design,
            existing_code=existing_code,
            test_results=test_results,
        )
        fixed_files = parse_generated_code_output(fixed_code_text)
        if fixed_files is not None:
            write_generated_files(code_dir, fixed_files)
        else:
            write_text_file(code_dir / "app.py", fixed_code_text)
        report_progress(f"Fix attempt {fix_attempts}/{max_fix_attempts}: code updated, re-running tests...")

        test_results, tests_passed = execute_tests(project_root)
        write_text_file(results_dir / "test_results.txt", test_results)
        report_progress(
            f"Fix attempt {fix_attempts}/{max_fix_attempts}: test run complete - "
            f"{'PASSED' if tests_passed else 'FAILED'}."
        )

    report_progress("Pipeline complete." if tests_passed else "Pipeline complete with remaining test failures.")

    # Step 6: Attempt to package the application into a self-contained artifact.
    report_progress("Step 6/6: Packaging application...")
    try:
        deploy_log, deploy_ok = package_application(project_root)
    except Exception as ex:  # defensive: ensure orchestrator never crashes on packaging
        deploy_log = f"Packaging raised an unexpected exception: {ex}"
        deploy_ok = False
    write_text_file(results_dir / "deployment.txt", deploy_log)
    report_progress(f"Step 6/6: Packaging {'SUCCEEDED' if deploy_ok else 'FAILED'}.")

    summary_lines = [
        f"Project directory: {project_root}",
        "Artifact generation completed.",
    ]
    if hl_clarification:
        summary_lines.append("High-level design was adjusted using user clarification.")
    if detailed_clarification:
        summary_lines.append("Detailed design was adjusted using user clarification.")
    if code_clarification:
        summary_lines.append("Code generation was adjusted using user clarification.")
    if tests_clarification:
        summary_lines.append("Test generation was adjusted using user clarification.")
    if fix_attempts:
        summary_lines.append(
            f"Code was automatically fixed {fix_attempts} time(s) based on test/runtime results."
        )
    if tests_passed:
        summary_lines.append("All tests passed.")
    else:
        summary_lines.append(f"Tests still failing after {fix_attempts} fix attempt(s).")
    summary_lines.append("Final test execution results are saved under results/test_results.txt.")
    summary_lines.append("\n" + test_results)

    return "\n".join(summary_lines)


def main() -> None:
    print("ideaToProd MCP server starting...")
    idea_name = input("Enter the idea name: ").strip()
    idea_description = input("Enter the idea description: ").strip()

    if not idea_name or not idea_description:
        print("Both idea name and idea description are required.")
        return

    result = orchestrate(idea_name, idea_description)
    print("\n=== MCP result ===\n")
    print(result)


if __name__ == "__main__":
    main()

