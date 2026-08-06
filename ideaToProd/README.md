# ideaToProd

`ideaToProd` is a local multi-agent orchestration platform that converts a software idea into a working Python project.

## What it does

The orchestrator in `ideaToProd_mcp.py` runs five agents sequentially:

1. `agent1_hl_design.py` - generate a high-level design from the idea.
2. `agent2_detailed_design.py` - create a detailed design from the high-level design.
3. `agent3_code_generation.py` - generate application code from the detailed design.
4. `agent4_unit_test_generation.py` - generate unit tests for the generated code.
5. `agent5_test_execution.py` - execute the generated unit tests and save results.

## Project structure

- `ideaToProd_mcp.py` - orchestrator entrypoint.
- `agent1_hl_design.py` - high-level design agent.
- `agent2_detailed_design.py` - detailed design agent.
- `agent3_code_generation.py` - code generation agent.
- `agent4_unit_test_generation.py` - unit test generation agent.
- `agent5_test_execution.py` - test execution agent.

Generated project output is written to a sibling folder named after the idea.

## Usage example

From the `ideaToProd` folder, run:

```bash
python ideaToProd_mcp.py
```

Then enter the idea name and description when prompted.

### Example input

- Idea name: `Smart Budget Helper`
- Idea description: `A simple Python app that summarizes a budget plan and displays a clear summary.`

### Example output

The orchestrator creates a new sibling directory named `Smart_Budget_Helper` with:

- `docs/high_level_design.md`
- `docs/detailed_design.md`
- `code/app.py`
- `tests/test_app.py`
- `results/test_results.txt`

The final console output includes the test execution summary.

## Notes

- The system uses local file storage only.
- If an agent output looks invalid, the orchestrator prompts for clarification.
- The generated code is simple and intended for demonstration.
