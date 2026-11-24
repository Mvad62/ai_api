---
kind: dependency_management
name: Python Dependencies via requirements.txt with .venv Isolation
category: dependency_management
scope:
    - '**'
source_files:
    - requirements.txt
    - .gitignore
---

## System / Approach

This is a small Python project that manages third-party dependencies exclusively through a single `requirements.txt` file and a local virtual environment (`.venv/`). There is no lockfile, no private registry configuration, and no vendoring of packages.

## Key Files

- `requirements.txt` — the sole dependency manifest listing three runtime libraries.
- `.gitignore` — excludes `.env`, `.venv/`, `__pycache__/`, and compiled bytecode (`*.py[cod]`) from version control.
- `.venv/` — the local virtual environment directory (ignored by git).

## Dependency Declarations

`requirements.txt` declares:

| Package | Version Constraint |
|---|---|
| `aiogram` | `>=3.7,<4.0` |
| `httpx` | `>=0.27,<1.0` |
| `python-dotenv` | `>=1.0,<2.0` |

All constraints use PEP 440 range specifiers: a lower bound (`>=`) plus an upper bound (`<`) to pin major versions while allowing minor/patch upgrades.

## Conventions and Constraints

- **Single manifest**: All third-party dependencies are declared in `requirements.txt`; there are no `setup.py`, `pyproject.toml`, `Pipfile`, or other Python packaging files in the repository root.
- **No lockfile**: There is no `requirements.lock`, `poetry.lock`, `Pipfile.lock`, or equivalent. The exact resolved versions are not committed; they live only in the local `.venv/`.
- **Virtual environment ignored**: `.venv/` is listed in `.gitignore`, so the environment is never tracked in version control.
- **No private registries or mirrors**: No `pip.conf`, `pip.ini`, `~/.config/pip/pip.conf`, `PYPI_URL`, or `--index-url` usage was found in the codebase; dependencies resolve against the default PyPI.
- **No vendored packages**: There is no `vendor/` directory or vendored third-party source.
- **Environment variables for secrets**: Secrets (e.g. API keys) are loaded via `python-dotenv` from a `.env` file, which is also gitignored (see `.gitignore`). An example template exists at `.env.example`.

## Scope

These patterns apply to this repository as a whole. Because the project is a flat Python script collection (no subpackages), the dependency surface is limited to the three packages listed above.