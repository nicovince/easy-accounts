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
    get_report,
    get_kdrive_api_url,
    ConfigError,
    ConfigValidationError,
    create_config_from_spreadsheet,
    validate_config_against_spreadsheet,
)
import easy_account.config as ea_config
import easy_account.infomaniak as infomaniak
from easy_account.infomaniak import InfomaniakApi, MissingTokenError

try:
    import argcomplete
except ImportError:
    argcomplete = None  # type: ignore


def make_completer(getter_func):
    """Factory for argparse completer methods"""

    def completer(prefix, parsed_args, **kwargs):
        try:
            config = load_config(parsed_args.config)
            choices = getter_func(config)
        except ConfigError:
            choices = []
        return (choice for choice in choices if choice.startswith(prefix))

    return completer


def add_cmn_args_parsers(parsers: list, config_path: Path):
    """Add args common to parsers"""

    for p in parsers:
        p.add_argument(
            "spreadsheet",
            type=str,
            help="Path to the banking accounts spreadsheet",
        )

        p.add_argument(
            "sheet",
            type=str,
            help="The title of the sheet to edit",
        )
        month_arg = p.add_argument(
            "month",
            type=str,
            help="The month the amount was spent",
        )
        month_arg.completer = make_completer(get_months)

        category_arg = p.add_argument(
            "category",
            type=str,
            help="The category of the amount spent",
        )
        category_arg.completer = make_completer(get_categories)

        user_arg = p.add_argument(
            "--user",
            type=str,
            default=None,
            help="In case of multi-user account, the user who made the expanse",
        )
        user_arg.completer = make_completer(get_users)


def parse_report_opt(report: str, current_month: str = None) -> tuple[str, str, str | None]:
    res = report.split(",")
    if len(res) == 1:
        category = res[0]
        month = current_month
    elif len(res) == 2:
        month = res[0] if res[0] else current_month
        category = res[1]
    elif len(res) == 3:
        month = res[0] if res[0] else current_month
        category = res[1]
        user = res[2] if res[2] else None
        return (month, category, user)
    else:
        raise ValueError(f"Invalid report format: {report}")
    return (month, category, None)


def account_get_cell_value(
    account: AccountSpreadsheet, month: str, category: str, user: str = None
):
    cell = account.get_cell(month, category, user)
    val = account.evaluate(cell)
    return (cell, val)


def validate_insert_show_args(args):
    # Validate that the spreadsheet exists
    spreadsheet_path = Path(args.spreadsheet)
    if not spreadsheet_path.exists():
        print(f"Error: Spreadsheet '{args.spreadsheet}' not found.", file=sys.stderr)
        sys.exit(1)

    # Validate config against spreadsheet if config file exists
    try:
        config = load_config(args.config)
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


def cmd_show(args):
    validate_insert_show_args(args)
    account = AccountSpreadsheet(args.spreadsheet)
    account.active_sheet = args.sheet
    cell, val = account_get_cell_value(account, args.month, args.category, args.user)
    print(f"Show content of {cell}: {val}")


def cmd_pull(args):
    api_url = args.api_url

    if api_url is None:
        try:
            config = load_config(args.config)
            api_url = get_kdrive_api_url(config)
        except ConfigError:
            pass

    if api_url is None:
        print(
            "Error: No API URL provided. Either provide the API URL as an argument "
            "or configure it in .easy-account.toml under [kdrive] api_url.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        destination = infomaniak.pull_file(api_url)
    except infomaniak.InfomaniakInvalidApiUrl:
        print(
            "Error: Invalid API URL format. Expected "
            "https://api.infomaniak.com/2/drive/<drive_id>/files/<file_id>",
            file=sys.stderr,
        )
        sys.exit(1)
    except infomaniak.MissingTokenError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except infomaniak.InfomaniakFileAlreadyExists as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloaded: {destination}")


def cmd_push(args):
    api_url = args.api_url

    if api_url is None:
        try:
            config = load_config(args.config)
            api_url = get_kdrive_api_url(config)
        except ConfigError:
            pass

    if api_url is None:
        print(
            "Error: No API URL provided. Either provide the API URL as an argument "
            "or configure it in .easy-account.toml under [kdrive] api_url.",
            file=sys.stderr,
        )
        sys.exit(1)

    parsed = api_url.rstrip("/").split("/")
    try:
        drive_id = int(parsed[-3])
        file_id = int(parsed[-1])
    except (IndexError, ValueError):
        print(
            "Error: Invalid API URL format. Expected "
            "https://api.infomaniak.com/2/drive/<drive_id>/files/<file_id>",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        api = InfomaniakApi()
    except MissingTokenError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    file_info = api.get_file_info(drive_id, file_id)
    local_file = Path(file_info.name)

    if not local_file.exists():
        print(f"Error: Local file not found: {local_file}", file=sys.stderr)
        sys.exit(1)

    api.upload_file(drive_id, file_id, str(local_file))
    print(f"Uploaded: {local_file}")


def cmd_insert(args):
    if args.verbose:
        spreadsheet_path = Path(args.spreadsheet)
        print(f"Processing spreadsheet: {spreadsheet_path.absolute()}")
        amounts_str = " + ".join(str(a) for a in args.amount)
        print(f"Adding {amounts_str} into category {args.category} for month {args.month}")
    print(f"Processing banking accounts from: {args.spreadsheet}")
    validate_insert_show_args(args)

    try:
        config = load_config(args.config)
    except ConfigError:
        config = None

    # Use default report from config if --report not specified
    if args.report is None:
        args.report = get_report(config, args.month)

    account = AccountSpreadsheet(args.spreadsheet)
    account.active_sheet = args.sheet
    if args.comment is not None:
        amounts_str = " + ".join(str(a) for a in args.amount)
        comment = f"{amounts_str} : {args.comment}"
    else:
        comment = None
    if not args.show_only:
        account.add_entry(args.month, args.category, args.amount, comment, args.user)
        account.save()
    else:
        cell, val = account_get_cell_value(account, args.month, args.category, args.user)
        print(f"Show content of {cell}: {val}")
    if args.report is not None:
        # args.report is now a list of report strings
        for report in args.report:
            (month, category, user) = parse_report_opt(report, args.month)
            cell, val = account_get_cell_value(account, month, category, user)
            print(f"{month} / {category}: {val}")


def main():
    """Main entry point for the easy-account CLI."""
    parser = argparse.ArgumentParser(
        prog="easy-account",
        description="Fill banking accounts spreadsheet from the command line",
        epilog=f"""
Configuration:
  This tool may use a {ea_config.DEFAULT_CFG_FILE} file in the current directory.
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
        const=ea_config.DEFAULT_CFG_FILE,
        metavar="SPREADSHEET",
        help="Create a configuration file. If a spreadsheet path is provided, "
        "extract months, categories and users from it.",
    )

    preparser = argparse.ArgumentParser(add_help=False)
    preparser.add_argument(
        "-c",
        "--config",
        type=str,
        help=f"Path to an alternative config file to {ea_config.DEFAULT_CFG_FILE}",
        default=ea_config.DEFAULT_CFG_FILE,
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help=f"Path to an alternative config file to {ea_config.DEFAULT_CFG_FILE}",
        default=ea_config.DEFAULT_CFG_FILE,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {importlib.metadata.version('easy-account')}",
    )

    # Handle --init flag early (before requiring positional arguments)
    if "--init" in sys.argv:
        args = parser.parse_args()
        config_path = Path(ea_config.DEFAULT_CFG_FILE)
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

    subparsers = parser.add_subparsers(help="Subcommands help")
    parser_insert = subparsers.add_parser(
        "insert", help="Insert new entry into account spreadsheet"
    )
    parser_show = subparsers.add_parser("show", help="Show cell value")
    parser_pull = subparsers.add_parser("pull", help="Download a file from Infomaniak kdrive")
    parser_push = subparsers.add_parser("push", help="Upload a file to Infomaniak kdrive")

    args, remaining = preparser.parse_known_args()
    add_cmn_args_parsers([parser_insert, parser_show], args.config)

    parser_insert.add_argument(
        "amount",
        type=float,
        nargs="+",
        help="Amount(s) spent to add into account",
    )

    parser_insert.add_argument(
        "--comment",
        type=str,
        default=None,
        help="A comment to the cell regarding the amount spent",
    )

    parser_insert.add_argument(
        "--report",
        type=str,
        nargs="+",
        default=None,
        help="Cell(s) for which the updated value must be reported. "
        "Format 'col-name,row-name[,user-name]'. Can be specified multiple times.",
    )

    parser_insert.add_argument(
        "--show-only", action="store_true", help="Only show content of requested cell and exit"
    )
    parser_insert.set_defaults(func=cmd_insert)
    parser_show.set_defaults(func=cmd_show)

    parser_pull.add_argument(
        "api_url",
        type=str,
        nargs="?",
        help="API URL of the file to download (e.g., https://api.infomaniak.com/2/drive/1475057/files/9)",
    )
    parser_pull.set_defaults(func=cmd_pull)

    parser_push.add_argument(
        "api_url",
        type=str,
        nargs="?",
        help="API URL of the file to upload (e.g., https://api.infomaniak.com/2/drive/1475057/files/9)",
    )
    parser_push.set_defaults(func=cmd_push)

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

    # Handle pull/push subcommand separately (doesn't require spreadsheet)
    if hasattr(args, "func") and args.func in (cmd_pull, cmd_push):
        args.func(args)
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
