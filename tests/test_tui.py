from unittest import mock
import argparse
import sys
import textual

from unittest.mock import MagicMock, patch
from easy_account.tui import EasyAccountTUI
import conftest


def test_tui_main_snap(snap_compare) -> None:
    """Test visual of the tui."""
    snap_compare("../easy_account/tui.py")


@mock.patch(
    "argparse.ArgumentParser.parse_args",
    return_value=argparse.Namespace(config=".easy-account.toml", spreadsheet=None),
)
async def test_tui_cli_opt(mock_args):
    """Test default options."""
    app = EasyAccountTUI()
    async with app.run_test():
        assert app.args.spreadsheet is None
        assert app.args.config == ".easy-account.toml"
        assert app.SUB_TITLE == "0.2.0"


def mock_ik_download_file(drive_id: int, file_id: int, destination: str) -> None:
    conftest.create_spreadsheet_template(destination)


def assert_select_menu(
    app: textual.app.App,
    select_name: str,
    disabled: bool,
    value: str | None = None,
):
    """Verify that a select menu has the valid properties.

    app: the app to query
    select_name: the name of the select menu to query
    disabled: whether the select menu should be disabled or not
    value: the expected value of the select menu, if not None
    """
    select = app.screen.query_one(f"#{select_name}")
    assert (
        select.disabled == disabled
    ), f"#{select_name} Select must be {'disabled' if disabled else 'enabled'}"
    if not disabled:
        if value is not None:
            assert select.value == value
        else:
            select.is_blank()


@mock.patch(
    "argparse.ArgumentParser.parse_args",
    return_value=argparse.Namespace(config=".easy-account.toml", spreadsheet=None),
)
async def test_tui_default_select_menu_state(mock_args):
    app = EasyAccountTUI()
    async with app.run_test():
        assert_select_menu(app, "sheet", True)
        assert_select_menu(app, "month", True)
        assert_select_menu(app, "category", True)
        assert_select_menu(app, "user", True)


async def test_tui_opt_spreadsheet(monkeypatch, tmp_path_cwd, spreadsheet_unmodified):
    """Test the option to specify the spreadsheet on the command line.

    Check the sheet selection menu is enabled"""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "easy-account-tui",
            "-f",
            spreadsheet_unmodified,
        ],
    )
    app = EasyAccountTUI()
    async with app.run_test():
        assert app.args.spreadsheet == spreadsheet_unmodified
        assert_select_menu(app, "sheet", False)
        print(app.screen.query_one("#sheet")._options)
        assert_select_menu(app, "month", True)
        assert_select_menu(app, "category", True)
        assert_select_menu(app, "user", True)


async def test_tui_pull(monkeypatch, tmp_path_cwd):
    """Test the pull button.

    Verify that the infomaniak api is called
    Verify that the sheet selection menu is enabled after the pull
    """
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
            ik_api_mock = MagicMock()
            ik_api_mock.get_file_info.return_value = mock_file_info
            ik_api_mock.download_file.side_effect = mock_ik_download_file
            InfomaniakApiMock.return_value = ik_api_mock

            await pilot.click("#pull")
            ik_api_mock.get_file_info.assert_called_once_with(3615, 1234)
            ik_api_mock.download_file.assert_called_once()
            assert app.args.spreadsheet == mock_file_info.name
            assert_select_menu(app, "sheet", False)
            assert_select_menu(app, "month", True)
            assert_select_menu(app, "category", True)
            assert_select_menu(app, "user", True)
