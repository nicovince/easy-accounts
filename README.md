# Easy Accounts

## Purpose

Fill banking accounts spreadsheet from the command line.

## Usage

```bash
easy-account insert <spreadsheet> <sheet> <month> <category> <amount> [<amount> ...] [OPTIONS]
easy-account show <spreadsheet> <sheet> <month> <category> [OPTIONS]
easy-account pull [api_url]
easy-account push [api_url]
```

### Arguments

- `<spreadsheet>`: Path to the banking accounts spreadsheet (Excel file)
- `<sheet>`: Title of the sheet to edit
- `<month>`: Month the amount was spent (e.g., "janvier", "fevrier")
- `<category>`: Category of the amount spent (e.g., "foo", "bar")
- `<amount>`: One or more amounts to add (space-separated floats)

### Options

#### `insert` options
- `--comment <text>`: Add a comment to the cell regarding the amount(s) spent
- `--show-only`: Show content of cell
- `--report <month,category[,user]>`: Report value of specific cell after insertion
- `--user <name>`: For multi-user accounts, specify the user who made the expense

#### Common options
- `-v, --verbose`: Enable verbose output
- `--version`: Show version information

### Pull and Push Commands

The `pull` and `push` commands allow you to synchronize files with Infomaniak kdrive.

#### `pull` command
Download a file from Infomaniak kdrive:
```bash
easy-account pull [api_url]
```

If `api_url` is not provided, it is read from the `kdrive.api_url` entry in `.easy-account.toml`.

The API URL format is: `https://api.infomaniak.com/2/drive/<drive_id>/files/<file_id>`

#### `push` command
Upload a file to Infomaniak kdrive:
```bash
easy-account push [api_url]
```

If `api_url` is not provided, it is read from the `kdrive.api_url` entry in `.easy-account.toml`.

The push command uploads the local file (determined by the file name from the API URL response) to kdrive.

Example:
```bash
easy-account pull https://api.infomaniak.com/2/drive/1475057/files/9
easy-account push https://api.infomaniak.com/2/drive/1475057/files/9
```

### Examples

Add a single amount:
```bash
easy-account insert accounts.xlsx Sheet1 janvier groceries 50.75 --comment "Weekly shopping"
```

Add multiple amounts to the same cell (creates formula: =5.0 + 10.5 + 15.3):
```bash
easy-account insert accounts.xlsx Sheet1 janvier groceries 5.0 10.5 15.3 --comment "Three purchases"
```

Multi-user account:
```bash
easy-account insert accounts.xlsx "multi users" janvier groceries 50.0 --user alice --comment "Alice's groceries"
```

With verbose output:
```bash
easy-account insert accounts.xlsx Sheet1 janvier groceries 100.0 -v
```

## Setup

### 1. Create Configuration File

First, create a `.easy-account.toml` configuration file in the directory where you'll run the command:

```bash
easy-account --init [spreadsheet.xlsx]
```

This creates an example configuration file with predefined months and categories. Edit it to match your needs:

```toml
# Easy Account Configuration
[months]
months = [
    "janvier",
    "fevrier",
    "mars",
    # ... add your months
]

[categories]
categories = [
    "groceries",
    "utilities",
    "rent",
    # ... add your categories
]

[users]
# Optional: list users for multi-user accounts
users = [
    "alice",
    "bob",
    "charlie",
]
```

### 2. Set Up Autocompletion (Optional but Recommended)

Enable shell autocompletion for bash/zsh:

```bash
eval "$(register-python-argcomplete easy-account)"
```

For **permanent** autocompletion, add the line above to your shell profile:

**For Bash** (~/.bashrc or ~/.bash_profile):
```bash
eval "$(register-python-argcomplete easy-account)"
```

**For Zsh** (~/.zshrc):
```bash
eval "$(register-python-argcomplete easy-account)"
```

After adding to your shell profile, restart your terminal or run `source ~/.bashrc` (or `source ~/.zshrc`).

Now you can use tab completion for month, category, and user arguments:
```bash
easy-account accounts.xlsx Sheet1 jan<TAB>  # auto-completes to janvier
easy-account accounts.xlsx Sheet1 janvier gr<TAB>  # auto-completes to groceries
easy-account accounts.xlsx Sheet1 janvier groceries 50 --user al<TAB>  # auto-completes to alice
```

### 3. Pre-commit Hooks

To set up pre-commit hooks that automatically run linting and formatting checks on commit, run:

```bash
pip install pre-commit
pre-commit install
```

This will configure Git hooks to automatically run Ruff linting and formatting on staged files before each commit.
