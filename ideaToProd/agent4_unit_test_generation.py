"""Agent 4: Generate unit tests for the generated code.
agno: ideaToProd
"""

AGNO = "ideaToProd"


def generate_unit_tests(code_text: str, clarification: str | None = None) -> str:
    if clarification:
        return (
            "import sys\n"
            "from pathlib import Path\n\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))\n\n"
            "from app import get_application_summary, run_application\n\n"
            "def test_summary_not_empty() -> None:\n"
            "    assert get_application_summary() != ''\n\n"
            "def test_run_application_returns_none() -> None:\n"
            "    assert run_application() is None\n\n"
            "# Clarification note: " + clarification
        )

    return (
        "import sys\n"
        "from pathlib import Path\n\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))\n\n"
        "from app import get_application_summary, run_application\n\n"
        "def test_summary_not_empty() -> None:\n"
        "    assert get_application_summary() != ''\n\n"
        "def test_run_application_returns_none() -> None:\n"
        "    assert run_application() is None\n"
    )
