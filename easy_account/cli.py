"""Command-line interface for easy-account."""

import argparse
import importlib.metadata
import sys
from pathlib import Path
from easy_account.account import AccountSpreadsheet


def main():
    """Main entry point for the easy-account CLI."""
    parser = argparse.ArgumentParser(
        prog="easy-account",
        description="Fill banking accounts spreadsheet from the command line",
    )

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

    parser.add_argument(
        "month",
        type=str,
        help="The month the amount was spent",
    )

    parser.add_argument(
        "category",
        type=str,
        help="The category of the amount spent",
    )

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

    parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="In case of multi-user account, the user who made the expanse",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {importlib.metadata.version('easy-account')}",
    )

    args = parser.parse_args()

    # Validate that the spreadsheet exists
    spreadsheet_path = Path(args.spreadsheet)
    if not spreadsheet_path.exists():
        print(f"Error: Spreadsheet '{args.spreadsheet}' not found.", file=sys.stderr)
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
