"""Command-line interface for easy-account."""

import argparse
import importlib.metadata
import sys
from pathlib import Path
from easy_account.account import AccountSpreadsheet
from easy_account.config import (
    load_config,
    get_months,
    get_categories,
    get_users,
    ConfigError,
    ConfigValidationError,
    create_config_from_spreadsheet,
    validate_config_against_spreadsheet,
)

try:
    import argcomplete
except ImportError:
    argcomplete = None  # type: ignore


def main():
    """Main entry point for the easy-account CLI."""
    parser = argparse.ArgumentParser(
        prog="easy-account",
        description="Fill banking accounts spreadsheet from the command line",
        epilog="""
Configuration:
  This tool requires a .easy-account.toml file in the current directory.
  Use 'easy-account --init' to create an example configuration file.

Autocompletion:
  To enable bash/zsh autocompletion, run:
    eval "$(register-python-argcomplete easy-account)"
  
  For permanent autocompletion, add the above line to your shell profile (.bashrc, .zshrc, etc.)
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--init",
        type=str,
        nargs="?",
        const=".easy-account.toml",
        metavar="SPREADSHEET",
        help="Create a configuration file. If a spreadsheet path is provided, "
        "extract months, categories and users from it.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {importlib.metadata.version('easy-account')}",
    )

    # Handle --init flag early (before requiring positional arguments)
    if "--init" in sys.argv:
        args = parser.parse_args()
        config_path = Path(".easy-account.toml")
        if config_path.exists():
            print(f"Configuration file already exists at {config_path.absolute()}")
            sys.exit(1)

        spreadsheet_path = args.init
        if spreadsheet_path:
            if not Path(spreadsheet_path).exists():
                print(f"Error: Spreadsheet '{spreadsheet_path}' not found.", file=sys.stderr)
                sys.exit(1)
            create_config_from_spreadsheet(spreadsheet_path, output_path=config_path)
            print(f"Configuration file created at {config_path.absolute()}")
            print("Months, categories, and users have been extracted from the spreadsheet.")
        else:
            from easy_account.config import create_example_config

            create_example_config(config_path)
            print(f"Example configuration file created at {config_path.absolute()}")
            print("Please edit it to match your needs and re-run the command.")
        sys.exit(0)

    # Add positional arguments
    parser.add_argument(
        "spreadsheet",
        type=str,
        help="Path to the banking accounts spreadsheet",
    )

    parser.add_argument(
        "sheet",
        type=str,
        help="The title of the sheet to edit",
    )

    # Try to load config for providing choices
    try:
        config = load_config()
        months_choices = get_months(config)
        categories_choices = get_categories(config)
        users_choices = get_users(config)
    except ConfigError:
        # Config file doesn't exist yet, allow any input
        months_choices = None
        categories_choices = None
        users_choices = None

    month_arg = parser.add_argument(
        "month",
        type=str,
        help="The month the amount was spent",
    )
    month_arg.completer = lambda prefix, parsed_args, **kwargs: months_choices or []  # type: ignore

    category_arg = parser.add_argument(
        "category",
        type=str,
        help="The category of the amount spent",
    )
    category_arg.completer = lambda prefix, parsed_args, **kwargs: categories_choices or []  # type: ignore

    parser.add_argument(
        "amount",
        type=float,
        nargs="+",
        help="Amount(s) spent to add into account",
    )

    parser.add_argument(
        "--comment",
        type=str,
        default=None,
        help="A comment to the cell regarding the amount spent",
    )

    user_arg = parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="In case of multi-user account, the user who made the expanse",
    )
    if users_choices:
        user_arg.completer = lambda prefix, parsed_args, **kwargs: users_choices or []  # type: ignore

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    # Enable argcomplete if available
    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # Validate that the spreadsheet exists
    spreadsheet_path = Path(args.spreadsheet)
    if not spreadsheet_path.exists():
        print(f"Error: Spreadsheet '{args.spreadsheet}' not found.", file=sys.stderr)
        sys.exit(1)

    # Validate config against spreadsheet if config file exists
    try:
        config = load_config()
    except ConfigError:
        config = None

    if args.user is not None:
        if config is not None:
            valid_users = get_users(config)
            if valid_users and args.user not in valid_users:
                print(
                    f"Error: User '{args.user}' not found in configuration file. "
                    f"Valid users are: {', '.join(valid_users)}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            validation_account = AccountSpreadsheet(args.spreadsheet)
            if args.sheet:
                validation_account.active_sheet = args.sheet
            spreadsheet_users = validation_account.get_spreadsheet_users()
            if spreadsheet_users and args.user not in spreadsheet_users:
                print(
                    f"Error: User '{args.user}' not found in spreadsheet. "
                    f"Valid users are: {', '.join(spreadsheet_users)}",
                    file=sys.stderr,
                )
                sys.exit(1)

    if config is not None:
        try:
            validate_config_against_spreadsheet(config, args.spreadsheet, args.sheet)
        except ConfigValidationError as e:
            print(f"Error: Configuration validation failed:\n{e}", file=sys.stderr)
            sys.exit(1)

    if args.verbose:
        print(f"Processing spreadsheet: {spreadsheet_path.absolute()}")
        amounts_str = " + ".join(str(a) for a in args.amount)
        print(f"Adding {amounts_str} into category {args.category} for month {args.month}")

    # Placeholder: actual implementation would go here
    print(f"Processing banking accounts from: {args.spreadsheet}")
    account = AccountSpreadsheet(args.spreadsheet)
    account.active_sheet = args.sheet
    if args.comment is not None:
        amounts_str = " + ".join(str(a) for a in args.amount)
        comment = f"{amounts_str} : {args.comment}"
    else:
        comment = None
    account.add_entry(args.month, args.category, args.amount, comment, args.user)
    account.save()


if __name__ == "__main__":
    main()
