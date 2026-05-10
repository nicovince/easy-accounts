---
name: pytest-tests
description: Guidance for implementing and updating pytest tests for the easy-account project
license: MIT
---

## Source-to-test file mapping

When modifying a source file, update its corresponding test file:

| Source file | Test file |
|---|---|
| `easy_account/spreadsheet.py` | `tests/test_spreadsheet.py` |
| `easy_account/account.py` | `tests/test_account_spreadsheet.py` |
| `easy_account/config.py` | `tests/test_config.py` |
| `easy_account/cli.py` | `tests/test_cli.py` |
| `easy_account/infomaniak.py` | `tests/test_infomaniak_api.py` |
| `easy_account/tui.py` | `tests/test_tui.py` |
| `easy_account/easy-account-tui.tcss` | `tests/__snapshots__/test_tui/` (update TUI snapshot) |

## Shared fixtures in `tests/conftest.py`

- `spreadsheet` — mutable copy of a template with "mono user" and "multi users" sheets
- `spreadsheet_unmodified` — integrity-checked copy (sha256 verified on teardown); use for read-only tests
- `monouser_account` / `multiuser_account_fixture` — for config validation tests
- `fresh_monouser_account` / `fresh_multiuser_account` — for user extraction tests
- `tmp_path_cwd` — temporarily sets cwd to tmp_path; use for CLI/config tests that write files
- `spreadsheet_template` (session-scoped) — shared template for all tests

Never create a tmp file under `/tmp`, uses at least `tmp_path` fixture.

Helper functions in conftest (import directly in test files):
- `get_months()` — returns month names list
- `get_categories()` — returns category names list
- `get_users()` — returns user names list
- `fill_monouser_sheet(ws)` — fills a worksheet with monouser layout
- `fill_multiuser_sheet(ws)` — fills a worksheet with multiuser layout
- `create_spreadsheet_template(filename)` — creates workbook with both sheets


## When adding a new source module

1. Create `tests/test_<module_name>.py`
2. Add fixtures to `tests/conftest.py` if the new module needs shared test data
3. Follow existing test patterns (same imports, assertion style, fixture usage)

## Testing conventions

- **Async**: `asyncio_mode = "auto"` in pyproject.toml — no need for `@pytest.mark.asyncio`
- **Snapshot tests** (TUI): use `snap_compare` fixture from `pytest-textual-snapshot`; SVGs stored in `tests/__snapshots__/test_tui/`
- **CLI tests**: use `CliRunner` from `click.testing`; pass config via `--config` flag or fixture
- **Config tests**: use `tmp_path_cwd` fixture and write `.easy-account.toml` to tmp_path
- **API tests**: use `responses` library to mock HTTP requests
- **Patches**: use `unittest.mock.patch` (not `mocker`)
- **Imports**: relative to project root (`from easy_account.<module> import <Class>`)

## Running tests

- All tests: `python -m pytest -v`
- Single file: `python -m pytest tests/test_<name>.py -v`
- Single test: `python -m pytest tests/test_<name>.py::test_<name> -v`
- Lint: `ruff check .`
- Format: `ruff format .`
