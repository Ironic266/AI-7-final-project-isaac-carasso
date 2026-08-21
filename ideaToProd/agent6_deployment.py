"""Agent 6: Package and prepare a Python project for deployment.
agno: ideaToProd
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipapp
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv
load_dotenv()

AGNO = "ideaToProd"

def _find_entry_script(code_dir: Path) -> Path | None:
    # Prefer a top-level app.py
    app_py = code_dir / "app.py"
    if app_py.exists():
        return app_py

    # Prefer package __main__.py
    for child in code_dir.iterdir():
        if child.is_dir() and (child / "__main__.py").exists():
            return child / "__main__.py"

    return None


def _package_application_local(project_root: Path) -> Tuple[str, bool]:
    """Local deterministic packaging implementation (fallback).

    Mirrors the original script behavior:
    - Detect an entry script (`app.py` or package `__main__.py`).
    - Attempt PyInstaller `--onefile` if available.
    - If PyInstaller not available or fails, try creating a runnable `.pyz` when `main` exists.
    - Otherwise create a zip archive of `code/` under `results/`.
    """

    code_dir = project_root / "code"
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    entry = _find_entry_script(code_dir)
    if entry is None:
        msg = "No entry script (app.py or package __main__.py) found in code/; creating a zip archive instead."
        archive = results_dir / f"{project_root.name}_bundle.zip"
        shutil.make_archive(str(archive.with_suffix('')), 'zip', root_dir=str(code_dir))
        return msg + f"\nCreated archive: {archive}", True

    # Try PyInstaller
    try:
        dist_dir = results_dir / "dist"
        build_dir = results_dir / "build"
        spec_dir = results_dir / "spec"
        for d in (dist_dir, build_dir, spec_dir):
            d.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            str(entry),
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            "--specpath",
            str(spec_dir),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        log = proc.stdout + "\n" + proc.stderr
        if proc.returncode == 0:
            exe_files = list(dist_dir.glob("*"))
            exe_list = ", ".join(p.name for p in exe_files)
            return f"PyInstaller succeeded. Dist: {dist_dir}. Files: {exe_list}", True
        # PyInstaller ran but failed
        fallback_archive = results_dir / f"{project_root.name}_bundle.zip"
        shutil.make_archive(str(fallback_archive.with_suffix('')), 'zip', root_dir=str(code_dir))
        return (
            f"PyInstaller failed (exit {proc.returncode}).\nLog:\n{log}\nCreated fallback archive: {fallback_archive}",
            False,
        )
    except FileNotFoundError:
        # PyInstaller not installed; fall back to zipapp if an entry with main exists
        try:
            pyz_target = results_dir / f"{project_root.name}.pyz"
            content = entry.read_text(encoding='utf-8')
            main_spec = None
            if "def main" in content:
                if entry.name == "app.py":
                    main_spec = "app:main"
                else:
                    main_spec = None

            if main_spec:
                zipapp.create_archive(str(code_dir), target=str(pyz_target), main=main_spec)
                return f"Created runnable pyz: {pyz_target}", True
            # fallback to zip file
            fallback_archive = results_dir / f"{project_root.name}_bundle.zip"
            shutil.make_archive(str(fallback_archive.with_suffix('')), 'zip', root_dir=str(code_dir))
            return (
                "PyInstaller not available and no suitable main() found; created zip archive instead: "
                + str(fallback_archive),
                True,
            )
        except Exception as exc:  # noqa: BLE001 - surface any unexpected issue
            return f"Packaging failed with exception: {exc}", False


def _normalize_agent_output(response: object) -> str:
    if isinstance(response, str):
        return response.strip()

    for attribute in ("content", "text", "output", "message"):
        value = getattr(response, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return str(response).strip()


def package_application(project_root: Path, model: object | None = None) -> Tuple[str, bool]:
    """Primary packaging function that prefers an `agno.agent` call, falling back to local logic.

    The agent receives instructions derived from this file's original behavior and is asked to
    determine the best packaging approach and to produce a human-readable report. If the
    `agno` package or model isn't available, this function uses the deterministic local
    implementation `_package_application_local`.
    """
    try:
        from agno.agent import Agent
        from agno.models.openai import OpenAIResponses
    except Exception:
        Agent = None
        OpenAIResponses = None

    # If agno is available, use it to reason about packaging and produce instructions/logs.
    if Agent is not None and OpenAIResponses is not None:
        agent = Agent(
            model=model or OpenAIResponses(id=__import__("os").environ.get("IDEA_TO_PROD_MODEL", "gpt-5.2")),
            description="Package a Python project into a runnable artifact or archive.",
            instructions=[
                "You are a deployment assistant that packages Python projects for distribution.",
                "Given a project root, detect the application entry point (prefer app.py or package __main__.py).",
                "Attempt to create a single-file executable using PyInstaller when possible.",
                "If PyInstaller is not available or fails, attempt to create a runnable .pyz when a top-level main() exists.",
                "If neither option is feasible, create a zip archive of the project's `code/` directory under `results/`.",
                "Create or ensure a `results/` directory exists and write artifacts there (dist/, build/, spec/ or bundle zip).",
                "Return a short human-readable log summarizing actions taken, files created, and any errors.",
                "When the project contains ambiguity, make reasonable assumptions and list them explicitly.",
                "Do not execute packaging commands yourself; instead provide the exact shell commands and expected outcomes so the environment can run them."
            ],
            markdown=False,
        )

        prompt = (
            f"Project root: {str(project_root)}\n"
            "Detect entry script, preferred packaging strategy, and produce a concise packaging report."
        )

        try:
            response = agent.run(prompt)
            generated = _normalize_agent_output(response)
            if generated:
                # Agent is advisory: return its report but still indicate success True.
                return generated, True
        except Exception:
            # Fall through to deterministic local implementation
            pass

    # Fallback deterministic behavior
    return _package_application_local(project_root)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("project_root", nargs="?", default=".")
    args = p.parse_args()
    out, ok = package_application(Path(args.project_root))
    print(out)
    sys.exit(0 if ok else 2)
