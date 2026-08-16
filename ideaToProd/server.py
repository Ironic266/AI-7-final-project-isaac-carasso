from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP
from ideaToProd_mcp import orchestrate 

#  1 - Initialization
server = FastMCP("IdeaToProd Service")


@server.tool()
def generate_code_and_tests(idea_name: str, idea_description: str) -> str:
    """
    Generate code and tests based on the provided idea name and description.
    """
    #  2 - Orchestration
    result = orchestrate(idea_name, idea_description)
    return result


if __name__ == "__main__":
    server.run()