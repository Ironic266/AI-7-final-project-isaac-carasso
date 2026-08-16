import sys
from pathlib import Path
import os

# Ensure ideaToProd module path is importable
sys.path.append(str(Path(__file__).resolve().parent / "ideaToProd"))

from ideaToProd_mcp import orchestrate

description = (
    "a simple python messagebox application showing an hourglass gif with configurable cycle speed. "
    "as part of this project resources copy the gif \"C:\\AI-7-final-project-isaac-carasso\\the-hourglass(200).gif\" "
    "to the projects /code/assets folder and use the copy in the code you generate. "
    "the frame rate of the gif will alter acording to user input of cycle-time in seconds. "
    "user input by selecting from dropdown list [2,5,10,30,60] or text box. do not allow \"< 1\" or \">120\" seconds. "
    "indicate current frame, cycle time and frame rate"
    "the last 5 frames must always run at 5 fps, regardless of user input. "
    "make sure all user input options effectively change the frame rate of the gif. and the displayed indications pdated accordingly."
)

if __name__ == '__main__':
    result = orchestrate("hourglass4", description)
    print("\n=== Orchestration Summary ===\n")
    print(result)
