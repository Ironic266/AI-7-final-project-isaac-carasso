
"""ideaToProd MCP orchestrator.

This server imports agents from separate local modules and orchestrates a 5-step
pipeline that creates a project folder, generates designs, writes code and tests,
and executes the resulting unit tests.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

from agent1_hl_design import create_hl_design
from agent2_detailed_design import create_detailed_design
from agent3_code_generation import generate_code
from agent4_unit_test_generation import generate_unit_tests
from agent5_test_execution import execute_tests


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
    return "def get_application_summary" in output and "def run_application" in output


def verify_tests(output: str) -> bool:
    return "def test_summary_not_empty" in output and "def test_run_application_returns_none" in output


def request_clarification(stage_name: str) -> str | None:
    print(f"\nClarification required for {stage_name}.")
    clarification = input("Please provide additional guidance, or press Enter to accept the generated artifact: ").strip()
    return clarification or None


def run_agent_with_verification(
    stage_name: str,
    action: Callable[..., str],
    validator: Callable[[str], bool],
    *args,
) -> tuple[str, str | None]:
    output = action(*args)
    if validator(output):
        return output, None

    clarification = request_clarification(stage_name)
    if clarification is None:
        return output, None

    output = action(*args, clarification=clarification)
    return output, clarification


def orchestrate(idea_name: str, idea_description: str) -> str:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent / safe_project_name(idea_name)
    create_project_structure(project_root)

    docs_dir = project_root / "docs"
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    results_dir = project_root / "results"

    hl_design, hl_clarification = run_agent_with_verification(
        "high-level design",
        create_hl_design,
        lambda output: verify_high_level_design(idea_name, idea_description, output),
        idea_name,
        idea_description,
    )
    remove_file_if_exists(docs_dir / "high_level_design.txt")
    write_text_file(docs_dir / "high_level_design.md", hl_design)

    detailed_design, detailed_clarification = run_agent_with_verification(
        "detailed design",
        create_detailed_design,
        verify_detailed_design,
        hl_design,
    )
    remove_file_if_exists(docs_dir / "detailed_design.txt")
    write_text_file(docs_dir / "detailed_design.md", detailed_design)

    code_text, code_clarification = run_agent_with_verification(
        "code generation",
        generate_code,
        verify_code,
        detailed_design,
    )
    write_text_file(code_dir / "app.py", code_text)

    tests_text, tests_clarification = run_agent_with_verification(
        "unit test generation",
        generate_unit_tests,
        verify_tests,
        code_text,
    )
    write_text_file(tests_dir / "test_app.py", tests_text)

    test_results = execute_tests(project_root)
    write_text_file(results_dir / "test_results.txt", test_results)

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

