"""Agent 5: Execute unit tests and return the results.
agno: ideaToProd
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import json

AGNO = "ideaToProd"
load_dotenv()


def _normalize_agent_output(response: object) -> str:
    if isinstance(response, str):
        return response.strip()

    for attribute in ("content", "text", "output", "message"):
        value = getattr(response, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return str(response).strip()


def _discover_test_files(tests_dir: Path) -> list[Path]:
    if not tests_dir.exists():
        return []

    candidates = {
        path
        for pattern in ("test_*.py", "*_test.py")
        for path in tests_dir.rglob(pattern)
        if path.is_file()
    }
    return sorted(candidates)


def _run_pytest(command: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str, float]:
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=env)
    duration = time.perf_counter() - start
    output = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
    return result.returncode, output, duration


def _default_human_readable_report(
    project_dir: Path,
    suite_return_code: int,
    suite_output: str,
    per_file_results: list[dict[str, object]],
) -> str:
    passed = sum(1 for item in per_file_results if item.get("status") == "PASS")
    failed = len(per_file_results) - passed

    lines = [
        "Agent 5 Test Execution Report",
        "=" * 30,
        "",
        f"Project: {project_dir}",
        f"Generated test files executed one by one: {len(per_file_results)}",
        "",
        "Overall suite run",
        "-" * 16,
        f"Status: {'PASS' if suite_return_code == 0 else 'FAIL'}",
        f"Return code: {suite_return_code}",
        "Output:",
        suite_output or "(no output)",
        "",
        "Per-file execution",
        "-" * 18,
        f"Passed: {passed}",
        f"Failed: {failed}",
        "",
    ]

    for index, item in enumerate(per_file_results, start=1):
        lines.extend(
            [
                f"{index}. {item['test_file']}",
                f"   Status: {item['status']}",
                f"   Return code: {item['return_code']}",
                f"   Duration: {item['duration_seconds']:.3f}s",
                "   Output:",
                (item.get("output") or "(no output)").replace("\n", "\n   "),
                "",
            ]
        )

    lines.append("End of report")
    return "\n".join(lines).strip() + "\n"


def execute_tests(
    project_dir: Path,
    clarification: str | None = None,
    model: object | None = None,
) -> str:
    code_dir = project_dir / "code"
    tests_dir = project_dir / "tests"
    results_dir = project_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(code_dir) + os.pathsep + existing_path

    suite_command = [sys.executable, "-m", "pytest", "-q", "tests"]
    suite_return_code, suite_output, _ = _run_pytest(suite_command, project_dir, env)

    per_file_results: list[dict[str, object]] = []
    for test_file in _discover_test_files(tests_dir):
        relative_test = test_file.relative_to(project_dir).as_posix()
        command = [sys.executable, "-m", "pytest", "-q", relative_test]
        return_code, output, duration = _run_pytest(command, project_dir, env)
        per_file_results.append(
            {
                "test_file": relative_test,
                "status": "PASS" if return_code == 0 else "FAIL",
                "return_code": return_code,
                "duration_seconds": duration,
                "output": output,
            }
        )

    default_report = _default_human_readable_report(
        project_dir=project_dir,
        suite_return_code=suite_return_code,
        suite_output=suite_output,
        per_file_results=per_file_results,
    )

    final_report = default_report
    try:
        from agno.agent import Agent
        from agno.models.openai import OpenAIResponses

        agent = Agent(
            model=model or OpenAIResponses(id=os.getenv("IDEA_TO_PROD_MODEL", "gpt-5.2")),
            description="Summarizes pytest execution into a human-readable report.",
            instructions=[
                "You are Agent 5 in the Idea-To-Prod platform.",
                "Use the provided execution data to produce a clear, human-readable test report.",
                "In addition to full-suite status, explicitly summarize each generated test file run one by one.",
                "Highlight total pass/fail counts and list failing tests first.",
                "Include a concise failure analysis and actionable next steps when failures exist.",
                "Do not invent execution outcomes; only use the supplied data.",
                "Output plain text only; do not use markdown code fences.",
            ],
            markdown=False,
        )

        payload = {
            "project_dir": str(project_dir),
            "suite": {
                "status": "PASS" if suite_return_code == 0 else "FAIL",
                "return_code": suite_return_code,
                "output": suite_output,
            },
            "per_file_results": per_file_results,
            "clarification": clarification,
        }

        response = agent.run(
            "Create a human-readable test report from the JSON execution data below.\n"
            "Use sections for overall suite, per-test-file results, and recommendations.\n"
            "Return only plain text.\n\n"
            f"{json.dumps(payload, indent=2)}"
        )
        generated = _normalize_agent_output(response)
        if generated:
            final_report = generated.strip() + "\n"
    except Exception:
        final_report = default_report

    report_path = results_dir / "test_results_human_readable.txt"
    report_path.write_text(final_report, encoding="utf-8")
    return final_report
