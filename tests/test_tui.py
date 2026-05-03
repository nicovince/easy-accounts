from unittest import mock
import argparse

from easy_account.tui import EasyAccountTUI


def test_tui_main_snap(snap_compare) -> None:
    snap_compare("../easy_account/tui.py")


@mock.patch(
    "argparse.ArgumentParser.parse_args",
    return_value=argparse.Namespace(config=".easy-account.toml", spreadsheet=None),
)
async def test_tui_cli_opt(mock_args):
    app = EasyAccountTUI()
    async with app.run_test():
        assert app.args.spreadsheet is None
        assert app.args.config == ".easy-account.toml"
