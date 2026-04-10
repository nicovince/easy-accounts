# AGENTS.md

## Commands

- **Run tests**: `python -m pytest -v`
- **Lint**: `ruff check .`
- **Format**: `ruff format .`
- **Run CLI**: `easy-account <command> ...` (requires `.easy-account.toml` in working directory)

## Entry Point

- CLI entry: `easy_account.cli:main` (defined in pyproject.toml)

## Setup Requirements

1. **Config file required**: Create `.easy-account.toml` before using the CLI:
   ```bash
   easy-account --init [spreadsheet.xlsx]
   ```
2. **Shell autocompletion** (optional): Add to shell profile:
   ```bash
   eval "$(register-python-argcomplete easy-account)"
   ```
3. **Pre-commit hooks** (optional):
   ```bash
   pre-commit install
   ```

## Notable Constraints

- Months and categories must be defined in `.easy-account.toml` - invalid values will fail
- Configuration file must be in the directory where the command runs (not in the package)
