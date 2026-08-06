"""Agent 5: Execute unit tests and return the results.
agno: ideaToProd
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

AGNO = "ideaToProd"


def execute_tests(project_dir: Path, clarification: str | None = None) -> str:
    code_dir = project_dir / "code"
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(code_dir) + os.pathsep + existing_path

    command = ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    result = subprocess.run(
        command,
        cwd=project_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    status = "PASS" if result.returncode == 0 else "FAIL"
    output = result.stdout.strip() + "\n" + result.stderr.strip()
    output = output.strip()

    summary = (
        f"Test execution status: {status}\n"
        f"Return code: {result.returncode}\n\n"
        f"{output}\n"
    )
    return summary
