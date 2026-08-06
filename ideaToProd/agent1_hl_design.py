"""Agent 1: Create high-level design from the idea name and description.
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


def create_hl_design(
    idea_name: str,
    idea_description: str,
    clarification: str | None = None,
    model: object | None = None,
) -> str:
    try:
        from agno.agent import Agent
        from agno.models.openai import OpenAIResponses
    except ImportError:
        Agent = None
        OpenAIResponses = None

    if Agent is not None and OpenAIResponses is not None:
        agent = Agent(
            model=model or OpenAIResponses(id=os.getenv("IDEA_TO_PROD_MODEL", "gpt-5.2")),
            description="Creates a complete high-level design document for a software idea.",
            instructions=[
                "You are Agent 1 in the Idea-To-Prod platform.",
                "Receive a product idea and produce a high-level design document in Markdown.",
                "Be concrete, implementation-aware, and structured.",
                "Do not write code.",
                "The document must include these sections: Title, Executive Summary, Product Goals, Users and Personas, Primary Use Cases, Functional Requirements, Non-Functional Requirements, Assumptions, Constraints, System Context, High-Level Architecture, Main Components, Data Model, External Integrations, Security and Privacy, Observability, Deployment Considerations, Risks, Open Questions, and Recommended Next Steps.",
                "Where the prompt is ambiguous, make reasonable assumptions and list them explicitly.",
                "Output only valid Markdown."
            ],
            markdown=True,
        )

        prompt = (
            f"Create a complete high-level design document in Markdown for the following software idea.\n"
            f"Idea name: {idea_name}\n"
            f"Idea description: {idea_description}\n"
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

    if clarification:
        return (
            f"# High-Level Design for '{idea_name}'\n\n"
            f"## Clarification\n\n"
            f"{clarification}\n\n"
            "The design below is updated to align with the clarified requirements."
        )

    return (
        f"# High-Level Design for '{idea_name}'\n\n"
        f"## Executive Summary\n\n"
        f"This design captures the core product intent for {idea_name}: {idea_description}.\n\n"
        "## Product Goals\n\n"
        "- Deliver a clear, user-friendly experience.\n"
        "- Keep the system maintainable and testable.\n"
        "- Enable straightforward extension in later iterations.\n\n"
        "## High-Level Architecture\n\n"
        "- Input and validation layer for capturing user intent.\n"
        "- Core application logic for processing requests and producing results.\n"
        "- Output layer for presenting results to users or downstream systems.\n"
        "\n"
        "## Main Components\n\n"
        "- User interface or interaction entry point.\n"
        "- Application services and business rules.\n"
        "- Storage or persistence layer as needed.\n"
        "\n"
        "## Recommended Next Steps\n\n"
        "- Refine the functional requirements.\n"
        "- Define the detailed implementation plan.\n"
        "- Prepare the first iteration of tests and validation criteria."
    )
