"""Agent 3: Generate Python application code from the detailed design.
agno: ideaToProd
"""

from __future__ import annotations
from dotenv import load_dotenv
import os

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


def _safe_class_name(text: str) -> str:
    cleaned = "".join(c for c in text.title() if c.isalnum())
    return cleaned or "GeneratedApp"


def generate_code(
    detailed_design: str,
    clarification: str | None = None,
    model: object | None = None,
) -> str:
    try:
        from agno.agent import Agent
        from agno.models.openai import OpenAIResponses
    except ImportError:
        raise

    agent = Agent(
        model=model or OpenAIResponses(id="gpt-5.2"),
        markdown=False,
        instructions=[
            "You are Agent 3 in the Idea-To-Prod platform: a senior software engineer that writes production-quality Python applications.",
            "You receive one document describing the application and its tasks, including actions for key, type, summary, and description.",
            "Generate a real implementation of the application described in the detailed design, using the tasks as the implementation plan.",
            "Do not invent unrelated features; implement only what the design requires.",
            "Return ONLY a single valid JSON object. No prose. No markdown code fences.",
            'JSON shape: {"files": [{"path": "relative/path", "content": "full file content"}], "summary": "one-line summary of what was implemented"}.',
            "Use idiomatic, working code with reasonable error handling and comments explaining non-obvious decisions.",
            "Prefer several small, focused files over one giant file. Include a test file when the task clearly benefits from one.",
            "Never invent Jira ticket details or GitHub metadata -- only write the application code itself.",
            "# Python coding standards\n- Follow the PEP 8 style guide.\n- Use type hints for all function signatures.\n- Write docstrings for public functions.\n- Use 4 spaces for indentation.",
        ],
    )

    prompt = (
        "Generate production-quality Python code for the application described below.\n"
        "Use the provided detailed design and task list to produce a real working implementation.\n"
        "Return only a single valid JSON object with files and summary.\n"
        "Do not include prose or markdown fences.\n\n"
        f"{detailed_design}\n"
    )
    if clarification:
        prompt += f"Additional clarification: {clarification}\n"

    try:
        response = agent.run(prompt)
    except Exception as exc:
        raise RuntimeError("Agent.run() failed while generating code") from exc

    generated = _normalize_agent_output(response)
    if generated:
        return generated
    raise RuntimeError("Agent returned no generated output from generate_code().")

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
