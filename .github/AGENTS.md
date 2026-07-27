# AGENTS.md

> Instructions for AI coding agents (GitHub Copilot, etc.) working in this repository.

---

## Project Overview

Provide a brief description of what this project does, its purpose, and its primary audience. Keep it concise — agents use this to understand the scope and intent of the codebase.

---

## Tech Stack

- **Language:** Python 3.11+
- **Package Manager:** `pip` / `poetry` / `uv` _(pick one)_
- **Virtual Environment:** `.venv` (local, not committed)
- **Testing:** `pytest`
- **Linting:** `ruff`
- **Formatting:** `black` or `ruff format`
- **Type Checking:** `mypy`
- **Task Runner:** `make` / `just` / custom scripts _(pick one)_

---

## Repository Structure

```
.
├── src/
│   └── your_package/       # Main application source code
│       ├── __init__.py
│       ├── core/           # Core business logic
│       ├── models/         # Data models / schemas
│       ├── services/       # Service layer
│       └── utils/          # Shared utilities
├── tests/
│   ├── unit/               # Unit tests (mirror src/ structure)
│   ├── integration/        # Integration tests
│   └── conftest.py         # Shared fixtures
├── scripts/                # Dev/ops helper scripts
├── docs/                   # Documentation
├── pyproject.toml          # Project metadata and tool config
├── requirements.txt        # Pinned dependencies (if not using poetry/uv)
├── .env.example            # Example environment variables
├── Makefile                # Common dev commands
└── AGENTS.md               # This file
```

---

## Getting Started

```bash
# Clone and set up
git clone <repo-url>
cd <repo>

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -e ".[dev]"
# or: poetry install
# or: uv sync
```

---

## Common Commands

| Task              | Command                          |
|-------------------|----------------------------------|
| Run tests         | `pytest`                         |
| Run with coverage | `pytest --cov=src`               |
| Lint              | `ruff check .`                   |
| Format            | `ruff format .` or `black .`     |
| Type check        | `mypy src/`                      |
| Run app           | `python -m your_package`         |
| All checks        | `make check` _(if Makefile exists)_ |

---

## Coding Standards

### Style
- Follow **PEP 8**. Formatting is enforced by `black`/`ruff format` — do not hand-format.
- Max line length: **88** characters (Black default).
- Use **double quotes** for strings.
- Imports are sorted by `isort` (configured in `pyproject.toml`).

### Type Hints
- **All** function signatures must have type hints — parameters and return types.
- Use `from __future__ import annotations` at the top of every module.
- Prefer `list[str]` over `List[str]`, `dict[str, int]` over `Dict[str, int]` (Python 3.10+ style).
- Use `TypeAlias`, `Protocol`, and `TypeVar` where appropriate.

```python
# ✅ Good
from __future__ import annotations

def process_items(items: list[str], limit: int = 10) -> dict[str, int]:
    ...

# ❌ Bad
def process_items(items, limit=10):
    ...
```

### Docstrings
- Use **Google-style docstrings** for all public functions, classes, and modules.
- Private helpers (prefixed `_`) may omit docstrings if intent is obvious.

```python
def fetch_user(user_id: int) -> User | None:
    """Fetch a user by their ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The User object if found, otherwise None.

    Raises:
        DatabaseError: If the database connection fails.
    """
```

### Error Handling
- Raise specific, descriptive exceptions — never bare `except:` or `except Exception:` silently.
- Define custom exceptions in `src/your_package/exceptions.py`.
- Always log errors with context before re-raising.

```python
# ✅ Good
try:
    result = risky_operation()
except ValueError as e:
    logger.error("risky_operation failed: %s", e)
    raise

# ❌ Bad
try:
    result = risky_operation()
except:
    pass
```

### Logging
- Use the standard `logging` module. Do **not** use `print()` for application output.
- Get loggers via `logger = logging.getLogger(__name__)`.
- Use structured log messages with `%s`-style formatting (not f-strings in log calls).

---

## Testing Guidelines

- Tests live in `tests/` and mirror the `src/` directory structure.
- Every new function or class must have a corresponding test.
- Use `pytest` fixtures (in `conftest.py`) for shared setup.
- Use `unittest.mock.patch` or `pytest-mock` for mocking external dependencies.
- Test naming: `test_<function>_<scenario>_<expected_result>`.

```python
# ✅ Good test name
def test_fetch_user_with_invalid_id_returns_none():
    ...

# ❌ Bad test name
def test_1():
    ...
```

- Aim for **>80% coverage** on `src/`. Coverage is checked in CI.
- Separate **unit** tests (no I/O, fully mocked) from **integration** tests (real I/O, marked `@pytest.mark.integration`).

---

## Environment Variables

- Never hardcode secrets or config values. Use environment variables.
- See `.env.example` for all required variables.
- Load env vars using `python-dotenv` or the app's config module — not `os.environ` scattered throughout the code.
- In tests, mock or override env vars using `monkeypatch.setenv(...)`.

---

## Agent-Specific Instructions

These rules apply specifically to AI coding agents generating or modifying code:

1. **Do not modify** `pyproject.toml`, `requirements.txt`, or lock files unless explicitly asked.
2. **Do not remove** existing tests. If refactoring, update tests to match.
3. **Always add type hints** — never generate untyped function signatures.
4. **Run linting mentally** before suggesting code — no unused imports, no shadowed variables.
5. **Prefer small, focused functions** — single responsibility, max ~40 lines per function.
6. **Do not introduce new dependencies** without flagging it explicitly in your response.
7. **Match the existing patterns** — look at neighboring files before generating new ones.
8. **Failing tests are a blocker** — do not suggest code that would break existing tests.
9. **Use `pathlib.Path`** for file system operations, not `os.path`.
10. **Use dataclasses or Pydantic** for structured data — not raw dicts.

---

## Pull Request Checklist

Before marking a PR ready for review, ensure:

- [ ] All tests pass (`pytest`)
- [ ] No lint errors (`ruff check .`)
- [ ] Code is formatted (`ruff format --check .`)
- [ ] Type checks pass (`mypy src/`)
- [ ] New functionality has test coverage
- [ ] Docstrings added for public API changes
- [ ] `.env.example` updated if new env vars were added
- [ ] No secrets or credentials committed

