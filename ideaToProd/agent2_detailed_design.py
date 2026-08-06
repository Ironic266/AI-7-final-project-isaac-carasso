"""Agent 2: Create detailed design from the high-level design.
agno: ideaToProd
"""

AGNO = "ideaToProd"


def create_detailed_design(high_level_design: str, clarification: str | None = None) -> str:
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
