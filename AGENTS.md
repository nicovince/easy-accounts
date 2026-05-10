# AGENTS.md

## Commands

- **Run tests**: `python -m pytest -v`
- **Run a single test**: `python -m pytest tests/test_file.py::test_name -v`
- **Lint**: `ruff check .`
- **Format**: `ruff format .`
- **Run CLI**: `easy-account <command> ...` (requires `.easy-account.toml` in CWD)
- **Run TUI**: `easy-account-tui`
- **Pre-commit**: `ruff check --fix` then `ruff-format` (via `.pre-commit-config.yaml`)

## Entry Points

- **CLI**: `easy_account.cli:main` → subcommands: `insert`, `show`, `pull`, `push`, `--init`, `--config`
- **TUI**: `easy_account.tui:main` → Textual app (requires API URL in config)

## Testing

- **Fixtures** in `tests/conftest.py` create temp xlsx workbooks (`spreadsheet`, `monouser_account`, `multiuser_account_fixture`, etc.)
- **Async tests** use `asyncio_mode = "auto"` (no need for `@pytest.mark.asyncio`)
- **Snapshot tests** (TUI) use `pytest-textual-snapshot` with `snap_compare` fixture; SVGs stored in `tests/__snapshots__/test_tui/`
- Test deps: `pytest`, `pytest-asyncio`, `pytest-textual-snapshot`

## Toolchain

- **Ruff** configured in `.ruff.toml`: target py310, line length 100, double quotes, select `E4/E7/E9/F/E501`
- **No typechecker** configured (no mypy/pyright)
- **Config required**: `.easy-account.toml` must exist in CWD (run `easy-account --init [file.xlsx]` to create)
- **Months and categories** must be defined in `.easy-account.toml` — invalid values fail at runtime
- **Formula evaluation** uses `openpyxl.formula.Tokenizer` with infix→postfix conversion
