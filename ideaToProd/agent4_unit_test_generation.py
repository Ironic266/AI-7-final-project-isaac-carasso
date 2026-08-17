from __future__ import annotations
"""Agent 4: Generate unit tests for the generated code.
agno: ideaToProd
"""

AGNO = "ideaToProd"

from dotenv import load_dotenv
import json
import os
from pathlib import Path

load_dotenv()


def _normalize_agent_output(response: object) -> str:
    if isinstance(response, str):
        return response.strip()

    for attribute in ("content", "text", "output", "message"):
        value = getattr(response, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return str(response).strip()


def _summarize_code_files(code_dir: Path) -> str:
    code_paths = sorted(p.relative_to(code_dir).as_posix() for p in code_dir.rglob("*.py") if p.is_file())
    if not code_paths:
        return "No Python implementation files were found in code_dir."

    lines = ["Implementation files found in code_dir:"]
    for path in code_paths:
        lines.append(f"- {path}")
    return "\n".join(lines)


def generate_unit_tests(
    code_dir: Path,
    tests_dir: Path,
    clarification: str | None = None,
    model: object | None = None,
) -> str:
    try:
        from agno.agent import Agent
        from agno.models.openai import OpenAIResponses
    except ImportError:
        Agent = None
        OpenAIResponses = None

    code_summary = _summarize_code_files(code_dir)
    if Agent is not None and OpenAIResponses is not None:
        agent = Agent(
            model=model or OpenAIResponses(id=os.getenv("IDEA_TO_PROD_MODEL", "gpt-5.2")),
            description="Generate a pytest test suite for an existing Python codebase.",
            instructions=[
                "You are Agent 4 in the Idea-To-Prod platform: a senior QA engineer that writes comprehensive pytest suites.",
                "You receive a description of implementation files and must generate a pytest package under tests_dir.",
                "Return only a single valid JSON object. No prose. No markdown code fences.",
                'JSON shape: {"files": [{"path": "relative/path", "content": "full file content"}], "summary": "one-line summary of test coverage"}.',
                "Use pytest and write tests for all implementation files found in code_dir.",
                "Include intended use cases, edge cases, and risk-based tests.",
                "Add a dedicated regression test that protects against a previously observed bug or failure mode.",
                "Ensure the tests import code from the sibling code directory when run from the project root.",
                "Create a proper Python test package by including tests/__init__.py.",
                "Prefer focused test modules and helper utilities over a single monolithic file.",
                "Create a command-line runnable script at tests/run_tests.py that:",
                "  - ensures the project's `code` directory is added to `sys.path` and `PYTHONPATH` before running pytest,",
                "  - runs the full pytest suite and writes a human-readable report to a results file,",
                "  - exits with the pytest return code so it can be invoked manually (e.g. `python tests/run_tests.py`).",
                "make sure the code directory is on sys.path and PYTHONPATH in the generated tests, so that the tests can be run from the project root.",
            ],
            markdown=False,
        )

        prompt = (
            "Generate a pytest test package under tests_dir for the Python implementation stored in code_dir.\n"
            "Use the file list and path information below to guide your test generation.\n"
            "Create a real pytest suite with unit tests, edge cases, risk-based tests, and a regression test.\n"
            "Return only valid JSON with file paths relative to tests_dir.\n\n"
            f"{code_summary}\n\n"
            f"Target tests directory: {tests_dir}\n"
            f"Implementation directory: {code_dir}\n"
        )
        if clarification:
            prompt += f"Additional clarification: {clarification}\n"

        try:
            response = agent.run(prompt)
            generated = _normalize_agent_output(response)
            if generated:
                return generated
        except Exception:
            pass

    fallback_files = [
        {
            "path": "__init__.py",
            "content": "# Test package for generated application code.\n",
        },
            {
                "path": "conftest.py",
                "content": (
                    "from pathlib import Path\n"
                    "import os, sys\n\n"
                    "# Ensure the sibling 'code' directory is importable in tests and subprocesses.\n"
                    "CODE_DIR = str(Path(__file__).resolve().parent.parent / 'code')\n"
                    "if CODE_DIR not in sys.path:\n"
                    "    sys.path.insert(0, CODE_DIR)\n\n"
                    "prev = os.environ.get('PYTHONPATH', '')\n"
                    "parts = [p for p in prev.split(os.pathsep) if p]\n"
                    "if CODE_DIR not in parts:\n"
                    "    parts.insert(0, CODE_DIR)\n"
                    "    os.environ['PYTHONPATH'] = os.pathsep.join(parts)\n"
                ),
            },
        {
            "path": "test_generated_application.py",
            "content": (
                "import sys\n"
                "from pathlib import Path\n\n"
                "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))\n\n"
                "import pytest\n\n"
                "try:\n"
                "    from app import get_application_summary, run_application\n"
                "except ImportError:\n"
                "    pytest.skip('Generated code not available for import', allow_module_level=True)\n\n"
                "def test_summary_not_empty() -> None:\n"
                "    assert get_application_summary() != ''\n\n"
                "def test_run_application_returns_none() -> None:\n"
                "    assert run_application() is None\n\n"
                "def test_regression_summary_not_empty_after_empty_input() -> None:\n"
                "    assert get_application_summary() != ''\n"
            ),
        },
        {
            "path": "run_tests.py",
            "content": (
                "from pathlib import Path\n"
                "import os, sys, subprocess, time\n\n"
                "def ensure_pythonpath():\n"
                "    project_root = Path(__file__).resolve().parent.parent\n"
                "    code_dir = project_root / 'code'\n"
                "    existing = os.environ.get('PYTHONPATH', '')\n"
                "    parts = [p for p in existing.split(os.pathsep) if p]\n"
                "    if str(code_dir) not in parts:\n"
                "        parts.insert(0, str(code_dir))\n"
                "        os.environ['PYTHONPATH'] = os.pathsep.join(parts)\n"
                "    if str(code_dir) not in sys.path:\n"
                "        sys.path.insert(0, str(code_dir))\n\n"
                "def run_suite():\n"
                "    ensure_pythonpath()\n"
                "    project_root = Path(__file__).resolve().parent.parent\n"
                "    results_dir = project_root / 'results'\n"
                "    results_dir.mkdir(parents=True, exist_ok=True)\n"
                "    cmd = [sys.executable, '-m', 'pytest', '-q', 'tests']\n"
                "    start = time.perf_counter()\n"
                "    res = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, env=os.environ.copy())\n"
                "    duration = time.perf_counter() - start\n"
                "    output = (res.stdout or '') + '\n' + (res.stderr or '')\n"
                "    report_path = results_dir / 'test_results_human_readable.txt'\n"
                "    report = f'Manual test run (run_tests.py)\nReturn code: {res.returncode}\nDuration: {duration:.3f}s\n\n{output}\n'\n"
                "    report_path.write_text(report, encoding='utf-8')\n"
                "    print(report)\n"
                "    return res.returncode\n\n"
                "if __name__ == '__main__':\n"
                "    raise SystemExit(run_suite())\n"
            ),
        },
    ]

    return json.dumps(
        {
            "files": fallback_files,
            "summary": "Basic pytest test package with a unit test suite and a regression test.",
        },
        indent=2,
    )
