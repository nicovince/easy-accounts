from unittest import mock
import argparse
import sys

from unittest.mock import MagicMock, patch
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
        assert app.SUB_TITLE == "0.2.0"


async def test_tui_pull(monkeypatch, tmp_path_cwd):
    config_path = tmp_path_cwd / ".easy-account.toml"
    config_content = """
[kdrive]
api_url = "https://api.infomaniak.com/2/drive/3615/files/1234"
"""
    config_path.write_text(config_content)
    monkeypatch.setenv("IK_TOKEN", "test_token")
    mock_file_info = MagicMock()
    mock_file_info.name = "test.xlsx"

    with patch.object(sys, "argv", []):
        app = EasyAccountTUI()
    async with app.run_test() as pilot:
        with patch("easy_account.infomaniak.InfomaniakApi") as InfomaniakApiMock:
            sheet_sel = app.screen.query_one("#sheet")
            assert sheet_sel.disabled, "#sheet Select must be disabled"

            ik_api_mock = MagicMock()
            ik_api_mock.get_file_info.return_value = mock_file_info
            ik_api_mock.download_file.return_value = None
            InfomaniakApiMock.return_value = ik_api_mock

            await pilot.click("#pull")
            ik_api_mock.get_file_info.assert_called_once_with(3615, 1234)
            ik_api_mock.download_file.assert_called_once()
            assert app.args.spreadsheet == mock_file_info.name
            assert not sheet_sel.disabled, "#sheet Select must be disabled"
