"""Command-line interface for easy-account."""

import argparse
import importlib.metadata
import sys
from pathlib import Path


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
        "-v", "--verbose",
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
        print(
            f"Error: Spreadsheet '{args.spreadsheet}' not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verbose:
        print(f"Processing spreadsheet: {spreadsheet_path.absolute()}")

    # Placeholder: actual implementation would go here
    print(f"Processing banking accounts from: {args.spreadsheet}")
    print("(This is a placeholder implementation)")


if __name__ == "__main__":
    main()
