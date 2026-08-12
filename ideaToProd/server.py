from fastmcp import FastMCP
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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