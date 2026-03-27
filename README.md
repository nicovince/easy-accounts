# Easy Accounts

## Purpose

Fill banking accounts spreadsheet from the command line.

## Usage

```bash
easy-account <spreadsheet> <sheet> <month> <category> <amount> [<amount> ...] [OPTIONS]
```

### Arguments

- `<spreadsheet>`: Path to the banking accounts spreadsheet (Excel file)
- `<sheet>`: Title of the sheet to edit
- `<month>`: Month the amount was spent (e.g., "janvier", "fevrier")
- `<category>`: Category of the amount spent (e.g., "foo", "bar")
- `<amount>`: One or more amounts to add (space-separated floats)

### Options

- `--comment <text>`: Add a comment to the cell regarding the amount(s) spent
- `--user <name>`: For multi-user accounts, specify the user who made the expense
- `-v, --verbose`: Enable verbose output
- `--version`: Show version information

### Examples

Add a single amount:
```bash
easy-account accounts.xlsx Sheet1 janvier groceries 50.75 --comment "Weekly shopping"
```

Add multiple amounts to the same cell (creates formula: =5.0 + 10.5 + 15.3):
```bash
easy-account accounts.xlsx Sheet1 janvier groceries 5.0 10.5 15.3 --comment "Three purchases"
```

Multi-user account:
```bash
easy-account accounts.xlsx "multi users" janvier groceries 50.0 --user alice --comment "Alice's groceries"
```

With verbose output:
```bash
easy-account accounts.xlsx Sheet1 janvier groceries 100.0 -v
```

## Setup

### Pre-commit Hooks

To set up pre-commit hooks that automatically run linting and formatting checks on commit, run:

```bash
pip install pre-commit
pre-commit install
```

This will configure Git hooks to automatically run Ruff linting and formatting on staged files before each commit.
