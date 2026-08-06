"""Agent 2: Create detailed design from the high-level design.
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


def create_detailed_design(
    high_level_design: str,
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
            description="Creates structured development tasks from a detailed design.",
            instructions=[
                "You are a planning agent that converts a detailed design into development work items.",
                "Return only valid JSON.",
                "Return an object with one top-level key named tasks.",
                "tasks must be an array.",
                "Each task must contain: summary, description, issue_type, phase, labels.",
                "issue_type should usually be Task, Story, or Sub-task.",
                "Descriptions must be implementation-ready and concise.",
                "Create tasks grouped across phases, with enough detail for Jira import."
            ],
            markdown=False,
        )

        prompt = (
            "Create a set of structured development tasks from the detailed design below:\n"
            f"{high_level_design}\n"
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
            "Detailed design updated with clarification:\n\n"
            f"Clarification: {clarification}\n\n"
            "1. Input handling\n"
            "   - Read the idea description and any additional user constraints.\n"
            "   - Validate text inputs and provide feedback.\n\n"
            "2. Domain model\n"
            "   - Define core entities and application state.\n\n"
            "3. Business logic and process flow\n"
            "   - Map the idea to a sequence of functions, data transformations, and outputs.\n\n"
            "4. Output and results\n"
            "   - Generate application output that is meaningful and testable.\n"
        )

    return (
        "Detailed design based on the high-level design:\n\n"
        "1. Requirements\n"
        "   - Capture the application idea and its main goals.\n"
        "   - Identify core user interactions and functional responsibilities.\n\n"
        "2. Module breakdown\n"
        "   - app.py: main application logic and orchestration.\n"
        "   - helpers: utility functions or process helpers if needed.\n\n"
        "3. Data flow\n"
        "   - Ingest idea description.\n"
        "   - Transform it into a structured summary and execution behavior.\n\n"
        "4. Validation and testing\n"
        "   - Keep the design simple enough to produce deterministic unit tests.\n\n"
        "The detailed design ensures the generated code is focused on the user idea with a clear structure."
    )
