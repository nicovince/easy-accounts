from unittest import mock
import argparse
import sys
import textual
import pytest

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
    opts: list | None = None,
    value: str | None = None,
):
    """Verify that a select menu has the valid properties.

    app: the app to query
    select_name: the name of the select menu to query
    disabled: whether the select menu should be disabled or not
    opts: The allowed options of the select menu, checked only if not None
    value: the expected value of the select menu
    """
    select = app.screen.query_one(f"#{select_name}")
    assert (
        select.disabled == disabled
    ), f"#{select_name} Select must be {'disabled' if disabled else 'enabled'}"

    if opts:
        for opt in opts:
            assert (opt, opt) in select._options
    if not disabled:
        if value is not None:
            assert select.value == value
        else:
            select.is_blank()


def assert_fetched_val(
    app: textual.app.App,
    fetched_name: str,
    value: str,
):
    """Verify a fetched value.

    app: the app to query
    fetched_name: The name of the fetched value widget
    value: The expected value
    """
    fetched_widget = app.screen.query_one(f"#{fetched_name}")
    assert fetched_widget.content == value


def get_select_index_by_value_name(select, value) -> int:
    return next(i for i, (p, v) in enumerate(select._options) if v == value)


async def menu_select(pilot, app: textual.app.App, select_name: str, value: str) -> None:
    """Change the value of a Select menu."""
    select = app.screen.query_one(f"#{select_name}")
    assert not select.disabled, f"#{select_name} cannot be disabled."
    option_index = get_select_index_by_value_name(select, value)
    selected_index = get_select_index_by_value_name(select, select.value)
    if selected_index:
        selected_index -= 1
    print(f"{selected_index=} {select.value=}")
    print(f"{option_index=} {value=}")
    await pilot.click(f"#{select_name}")
    for _ in range(selected_index):
        await pilot.press("up")
    for _ in range(option_index + 1):
        await pilot.press("down")
    await pilot.press("enter")
    await pilot.pause()
    assert select.value == value


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


@pytest.fixture(scope="session")
def default_tui_easy_account_cfg(tmp_path_factory):
    """Fixture to create a default configuration file."""
    config_path = tmp_path_factory.mktemp("template") / ".easy-account.toml"
    config_content = """
[tui]
total_spent_category = "total-out"
total_income_category = "total-in"
balance_category = "net"
"""
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def tui_app_opt_spreadsheet(monkeypatch, default_tui_easy_account_cfg, spreadsheet_unmodified):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "easy-account-tui",
            "-c",
            default_tui_easy_account_cfg,
            "-f",
            spreadsheet_unmodified,
        ],
    )
    app = EasyAccountTUI()
    return app


async def test_tui_opt_spreadsheet(tui_app_opt_spreadsheet, spreadsheet_unmodified):
    """Test the option to specify the spreadsheet on the command line.

    Check the sheet selection menu is enabled"""
    app = tui_app_opt_spreadsheet
    async with app.run_test():
        assert app.args.spreadsheet == spreadsheet_unmodified
        assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
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
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            assert_select_menu(app, "month", True)
            assert_select_menu(app, "category", True)
            assert_select_menu(app, "user", True)


async def test_tui_select_sheet_monouser(tui_app_opt_spreadsheet):
    """Test sheet selection with monouser."""
    app = tui_app_opt_spreadsheet
    async with app.run_test() as pilot:
        assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
        await menu_select(pilot, app, "sheet", "mono user")
        assert_select_menu(app, "month", False, conftest.get_months(), None)
        assert_select_menu(app, "category", False, conftest.get_categories(), None)
        assert_select_menu(app, "user", True)


async def test_tui_select_sheet_multiuser(tui_app_opt_spreadsheet):
    """Test sheet selection with multiusers."""
    app = tui_app_opt_spreadsheet
    async with app.run_test() as pilot:
        assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
        await menu_select(pilot, app, "sheet", "multi users")
        assert_select_menu(app, "month", False, conftest.get_months(), None)
        assert_select_menu(app, "category", False, conftest.get_categories(), None)
        assert_select_menu(app, "user", False, conftest.get_users(), None)


async def test_tui_select_sheet_multiuser_to_monouser(tui_app_opt_spreadsheet):
    """Test sheet selection

    Check the users are cleared if selecting a monouser sheet afeer a multiuser's
    """
    app = tui_app_opt_spreadsheet
    async with app.run_test() as pilot:
        await menu_select(pilot, app, "sheet", "multi users")
        assert_select_menu(app, "user", False, conftest.get_users(), None)
        await menu_select(pilot, app, "sheet", "mono user")
        assert_select_menu(app, "user", True)


async def test_tui_all_out_value(tui_app_opt_spreadsheet):
    """Test the all out informational value."""
    app = tui_app_opt_spreadsheet
    async with app.run_test(size=(100, 50)) as pilot:
        assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
        await menu_select(pilot, app, "sheet", "mono user")
        assert_select_menu(app, "month", False, conftest.get_months(), None)
        await menu_select(pilot, app, "month", "janvier")
        assert_fetched_val(app, "spent_value", "1234")


async def test_tui_all_in_value(tui_app_opt_spreadsheet):
    """Test the all in informational value."""
    app = tui_app_opt_spreadsheet
    async with app.run_test(size=(100, 50)) as pilot:
        assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
        await menu_select(pilot, app, "sheet", "mono user")
        assert_select_menu(app, "month", False, conftest.get_months(), None)
        await menu_select(pilot, app, "month", "fevrier")
        assert_fetched_val(app, "income_value", "111")


async def test_tui_balance_value(tui_app_opt_spreadsheet):
    """Test the balance informational value."""
    app = tui_app_opt_spreadsheet
    async with app.run_test(size=(100, 50)) as pilot:
        assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
        await menu_select(pilot, app, "sheet", "mono user")
        assert_select_menu(app, "month", False, conftest.get_months(), None)
        await menu_select(pilot, app, "month", "janvier")
        assert_fetched_val(app, "balance", "-1000")
