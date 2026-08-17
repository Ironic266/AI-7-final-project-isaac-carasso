from __future__ import annotations

import shutil
import subprocess
import sys
import zipapp
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv
load_dotenv()

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


def package_application(project_root: Path) -> Tuple[str, bool]:
    """Attempt to produce a self-contained executable for the project.

    Strategy:
    - If PyInstaller is available, run `pyinstaller --onefile` on a detected entry script.
    - If PyInstaller is not available or fails, fall back to creating a zip archive of
      the `code` folder under `results/` (not strictly an executable, but portable).

    Returns a tuple of (human-readable log, success_flag).
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
            # Try to make a .pyz if the top-level app module defines main
            pyz_target = results_dir / f"{project_root.name}.pyz"
            # zipapp requires a main 'module:callable' if we want an executable entrypoint.
            # If app.py exists and defines `main`, try to use it.
            content = entry.read_text(encoding='utf-8')
            main_spec = None
            if "def main" in content:
                # assume app:main
                if entry.name == "app.py":
                    main_spec = "app:main"
                else:
                    # if entry is package/__main__.py, can't easily reference it; skip
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


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("project_root", nargs="?", default=".")
    args = p.parse_args()
    out, ok = package_application(Path(args.project_root))
    print(out)
    sys.exit(0 if ok else 2)
