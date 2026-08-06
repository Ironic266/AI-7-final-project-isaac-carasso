"""Agent 3: Generate Python application code from the detailed design.
agno: ideaToProd
"""

from __future__ import annotations

AGNO = "ideaToProd"


def _safe_class_name(text: str) -> str:
    cleaned = "".join(c for c in text.title() if c.isalnum())
    return cleaned or "GeneratedApp"


def generate_code(detailed_design: str, clarification: str | None = None) -> str:
    idea_name = "Generated Application"
    for line in detailed_design.splitlines():
        if "for '" in line:
            start = line.find("for '") + 5
            end = line.find("'", start)
            if end > start:
                idea_name = line[start:end]
                break

    class_name = _safe_class_name(idea_name)
    if clarification:
        return (
            f"# Generated application code for '{idea_name}' with clarification:\n"
            f"# {clarification}\n\n"
            "def get_application_summary() -> str:\n"
            f"    return 'This revised version of {idea_name} reflects the clarified requirements.'\n\n"
            "def run_application() -> None:\n"
            "    summary = get_application_summary()\n"
            "    print(summary)\n\n"
            "if __name__ == '__main__':\n"
            "    run_application()\n"
        )

    return (
        "# Generated Python application code\n"
        "def get_application_summary() -> str:\n"
        f"    return 'This application implements the design for {idea_name}.'\n\n"
        "def run_application() -> None:\n"
        "    summary = get_application_summary()\n"
        "    print(summary)\n\n"
        "if __name__ == '__main__':\n"
        "    run_application()\n"
    )
