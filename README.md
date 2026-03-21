# Easy Accounts

## Purpose

Fill banking accounts spreadsheet from the command line.

```bash
easy-account <spreadsheet>
```

## Setup

### Pre-commit Hooks

To set up pre-commit hooks that automatically run linting and formatting checks on commit, run:

```bash
pip install pre-commit
pre-commit install
```

This will configure Git hooks to automatically run Ruff linting and formatting on staged files before each commit.
