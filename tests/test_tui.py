from unittest import mock
import argparse
import sys
import textual
import math
import pytest
import logging

from unittest.mock import MagicMock, patch
from easy_account.tui import EasyAccountTUI
from easy_account.account import AccountSpreadsheet
from textual.widgets import Input
import conftest


def test_tui_main_snap(snap_compare) -> None:
    """Test visual of the tui."""
    assert snap_compare("../easy_account/tui.py")


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


async def pilot_press(pilot: textual.app.App, key: str) -> None:
    """Log and pilot key."""
    logging.debug(f"pilot[{key}]")
    await pilot.press(key)


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


def get_select_index_by_value_name(select, value) -> int:
    """Get the index of a select option by its value."""
    logging.debug(f"{select._options}")
    return next(i for i, (p, v) in enumerate(select._options) if v == value)


async def menu_select(pilot, app: textual.app.App, select_name: str, value: str) -> None:
    """Change the value of a Select menu."""
    select = app.screen.query_one(f"#{select_name}")
    assert not select.disabled, f"#{select_name} cannot be disabled."
    option_index = get_select_index_by_value_name(select, value)
    selected_index = get_select_index_by_value_name(select, select.value)
    logging.info(
        f"Currently selected {select.value} in #{select_name} select menu at index {selected_index}"
    )
    logging.info(f"Selecting {value} in #{select_name} select menu at index {option_index}")
    if selected_index:
        if option_index < selected_index:
            delta = option_index - selected_index - 1
        else:
            delta = option_index - selected_index + 1
    else:
        delta = option_index + 1
    logging.info(f"delta: {delta}")

    await pilot.click(f"#{select_name}")
    if delta > 0:
        key = "down"
    else:
        key = "up"
    for _ in range(int(math.fabs(delta))):
        await pilot_press(pilot, key)
    await pilot_press(pilot, "enter")
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
def simple_tui_easy_account_cfg(tmp_path_factory):
    """Fixture to create a default configuration file."""
    config_path = tmp_path_factory.mktemp("template") / ".easy-account.toml"
    config_content = """
[tui]
total_spent_category = "all-out"
total_income_category = "all-in"
balance_category = "balance"
"""
    config_path.write_text(config_content)
    return str(config_path)


def launch_app():
    logging.info("Command line: %s", " ".join(sys.argv))
    app = EasyAccountTUI()
    return app


@pytest.fixture
def tui_app_nocfg_spreadsheet(monkeypatch, spreadsheet_unmodified):
    """Launch app with a default config file."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "easy-account-tui",
            "-f",
            spreadsheet_unmodified,
        ],
    )
    return launch_app()


@pytest.fixture
def tui_app_opt_spreadsheet(monkeypatch, simple_tui_easy_account_cfg, spreadsheet_unmodified):
    """Launch app with a default config file."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "easy-account-tui",
            "-c",
            simple_tui_easy_account_cfg,
            "-f",
            spreadsheet_unmodified,
        ],
    )
    return launch_app()


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


class TestTuiSelect:
    """Test the various Select widgets."""

    async def test_tui_select_sheet_monouser(self, tui_app_opt_spreadsheet):
        """Test sheet selection with monouser."""
        app = tui_app_opt_spreadsheet
        async with app.run_test() as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "mono user")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            assert_select_menu(app, "category", False, conftest.get_categories(), None)
            assert_select_menu(app, "user", True)

    async def test_tui_select_sheet_multiuser(self, tui_app_opt_spreadsheet):
        """Test sheet selection with multiusers."""
        app = tui_app_opt_spreadsheet
        async with app.run_test() as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "multi users")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            assert_select_menu(app, "category", False, conftest.get_categories(), None)
            assert_select_menu(app, "user", False, conftest.get_users(), None)

    async def test_tui_select_sheet_multiuser_to_monouser(self, tui_app_opt_spreadsheet):
        """Test sheet selection

        Check the users are cleared if selecting a monouser sheet afeer a multiuser's
        """
        app = tui_app_opt_spreadsheet
        async with app.run_test() as pilot:
            await menu_select(pilot, app, "sheet", "multi users")
            assert_select_menu(app, "user", False, conftest.get_users(), None)
            await menu_select(pilot, app, "sheet", "mono user")
            assert_select_menu(app, "user", True)


class TestTuiDisplayedValues:
    """Test values displayed in Static Widgets."""

    @staticmethod
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

    @classmethod
    def assert_all_fetched_val(
        cls,
        app: textual.app.App,
        spent: str,
        income: str,
        balance: str,
    ) -> None:
        """Verify all displayed values."""
        cls.assert_fetched_val(app, "spent_value", spent)
        cls.assert_fetched_val(app, "income_value", income)
        cls.assert_fetched_val(app, "balance", balance)

    async def test_tui_all_out_value(self, tui_app_opt_spreadsheet):
        """Test the all out informational value."""
        app = tui_app_opt_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "mono user")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            await menu_select(pilot, app, "month", "janvier")
            self.assert_fetched_val(app, "spent_value", "1234")

    async def test_tui_all_in_value(self, tui_app_opt_spreadsheet):
        """Test the all in informational value."""
        app = tui_app_opt_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "mono user")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            await menu_select(pilot, app, "month", "fevrier")
            self.assert_fetched_val(app, "income_value", "111")

    async def test_tui_balance_value(self, tui_app_opt_spreadsheet):
        """Test the balance informational value."""
        app = tui_app_opt_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "mono user")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            await menu_select(pilot, app, "month", "janvier")
            self.assert_fetched_val(app, "balance", "-1000")

    async def test_tui_fetched_val_no_cfg(self, tui_app_nocfg_spreadsheet):
        """Test the app when no config file is provided."""
        app = tui_app_nocfg_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "mono user")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            await menu_select(pilot, app, "month", "janvier")
            self.assert_all_fetched_val(app, "N/A", "N/A", "N/A")

    async def test_tui_multiuser_fetched_val_no_user_selected(self, tui_app_opt_spreadsheet):
        """Test fetched vals for multiuser sheets.

        Test fetched vals reports N/A when user is not selected yet.
        """
        app = tui_app_opt_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            assert_select_menu(app, "sheet", False, ["mono user", "multi users"], None)
            await menu_select(pilot, app, "sheet", "multi users")
            assert_select_menu(app, "month", False, conftest.get_months(), None)
            await menu_select(pilot, app, "month", "janvier")
            self.assert_all_fetched_val(app, "N/A", "N/A", "N/A")

    async def test_tui_multiuser_january_fetched_val_user_selected(self, tui_app_opt_spreadsheet):
        """Test fetched vals for multiuser sheets.

        Test fetched vals reports accurate values on user selection
        """
        app = tui_app_opt_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app, "sheet", "multi users")
            await menu_select(pilot, app, "month", "janvier")
            await menu_select(pilot, app, "user", "alice")
            self.assert_all_fetched_val(app, "100", "150", "50")
            await menu_select(pilot, app, "user", "bob")
            self.assert_all_fetched_val(app, "200", "220", "20")
            await menu_select(pilot, app, "user", "shared")
            self.assert_all_fetched_val(app, "300", "360", "60")

    async def test_tui_multiuser_december_fetched_val_user_selected(self, tui_app_opt_spreadsheet):
        """Test fetched vals for multiuser sheets.

        Test fetched vals reports accurate values on user selection
        """
        app = tui_app_opt_spreadsheet
        async with app.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app, "sheet", "multi users")
            await menu_select(pilot, app, "month", "decembre")
            await menu_select(pilot, app, "user", "alice")
            self.assert_all_fetched_val(app, "1200", "1212", "12")
            await menu_select(pilot, app, "user", "bob")
            self.assert_all_fetched_val(app, "2400", "2424", "24")
            await menu_select(pilot, app, "user", "shared")
            self.assert_all_fetched_val(app, "3600", "3636", "36")


class TestTuiNewEntry:
    """Test modifications of files by using the amount/comment/validate widgets."""

    @pytest.fixture
    def app(self, monkeypatch, simple_tui_easy_account_cfg, spreadsheet):
        """Launch app with a default config file."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account-tui",
                "-c",
                simple_tui_easy_account_cfg,
                "-f",
                spreadsheet,
            ],
        )
        return launch_app()

    async def modify_input(self, pilot: textual.app.App, name: str, value: str):
        """Modify an Input widget with the requested value."""
        await pilot.click(f"#{name}")
        await pilot.press(*[c for c in value])
        widget = pilot.app.screen.query_one(f"#{name}")
        assert widget.value == value

    async def validate(self, pilot: textual.app.App):
        """Click the Validate button."""
        await pilot.click("#confirm")

    async def fill_new_entry(
        self,
        pilot: textual.app.App,
        sheet: str,
        month: str,
        category: str,
        amount: str,
        comment: str | None = None,
        user: str | None = None,
    ):
        """Fill and submit a new entry form."""
        await menu_select(pilot, pilot.app, "sheet", sheet)
        await menu_select(pilot, pilot.app, "month", month)
        await menu_select(pilot, pilot.app, "category", category)
        if user:
            await menu_select(pilot, pilot.app, "user", user)
        await self.modify_input(pilot, "amount", amount)
        if comment is not None:
            await self.modify_input(pilot, "comment", comment)
        await self.validate(pilot)

    def assert_cell(
        self,
        spreadsheet: str,
        sheet: str,
        month: str,
        category: str,
        expected_value: str,
        expected_comment: str | None = None,
        user: str | None = None,
    ):
        """Assert the value and comment of a cell."""
        account = AccountSpreadsheet(spreadsheet)
        account.active_sheet = sheet
        c = account.get_cell(month=month, category=category, user=user)
        assert c.value == expected_value
        if expected_comment is not None:
            assert c.comment is not None
            assert c.comment.text == expected_comment
        else:
            assert c.comment is None

    async def test_tui_add_new_entry(self, app, spreadsheet):
        """Test adding a new entry with an amount."""
        async with app.run_test(size=(100, 50)) as pilot:
            await self.fill_new_entry(
                pilot,
                "mono user",
                "janvier",
                "out-foo",
                "15",
            )
        self.assert_cell(
            spreadsheet,
            "mono user",
            "janvier",
            "out-foo",
            "=15",
        )

    async def test_tui_add_new_entry_with_comment(self, app, spreadsheet):
        """Test adding a new entry with an amount and a comment."""
        async with app.run_test(size=(100, 50)) as pilot:
            await self.fill_new_entry(
                pilot,
                "mono user",
                "janvier",
                "out-foo",
                "15",
                comment="test comment",
            )
        self.assert_cell(
            spreadsheet,
            "mono user",
            "janvier",
            "out-foo",
            "=15",
            expected_comment="test comment",
        )

    async def test_tui_add_new_entry_negative_amount(self, app, spreadsheet):
        """Test adding a negative amount produces a float cell value."""
        async with app.run_test(size=(100, 50)) as pilot:
            await self.fill_new_entry(
                pilot,
                "mono user",
                "janvier",
                "out-foo",
                "-15",
            )
        self.assert_cell(
            spreadsheet,
            "mono user",
            "janvier",
            "out-foo",
            "=-15.0",
        )

    async def test_tui_add_new_entry_append(self, app, spreadsheet):
        """Test appending an amount to an existing cell formula."""
        async with app.run_test(size=(100, 50)) as pilot:
            await self.fill_new_entry(
                pilot,
                "mono user",
                "janvier",
                "out-bar",
                "5",
            )
        self.assert_cell(
            spreadsheet,
            "mono user",
            "janvier",
            "out-bar",
            "=1234 + 5",
        )

    async def test_tui_add_new_entry_append_comment(self, app, spreadsheet):
        """Test appending a comment to an existing cell comment."""
        async with app.run_test(size=(100, 50)) as pilot:
            await self.fill_new_entry(
                pilot,
                "mono user",
                "janvier",
                "out-foo",
                "10",
                comment="first comment",
            )
        app2 = launch_app()
        async with app2.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app2, "sheet", "mono user")
            await menu_select(pilot, app2, "month", "janvier")
            await menu_select(pilot, app2, "category", "out-foo")
            await self.modify_input(pilot, "amount", "20")
            await self.modify_input(pilot, "comment", "second comment")
            await self.validate(pilot)
        self.assert_cell(
            spreadsheet,
            "mono user",
            "janvier",
            "out-foo",
            "=10 + 20",
            expected_comment="first comment\nsecond comment",
        )

    async def test_tui_add_new_entry_multiuser_comment(self, app, spreadsheet):
        """Test adding an entry with a comment on a multi-user sheet."""
        async with app.run_test(size=(100, 50)) as pilot:
            await self.fill_new_entry(
                pilot,
                "multi users",
                "janvier",
                "out-foo",
                "50",
                comment="alice entry",
                user="alice",
            )
        self.assert_cell(
            spreadsheet,
            "multi users",
            "janvier",
            "out-foo",
            "=50",
            expected_comment="alice entry",
            user="alice",
        )

    async def test_tui_add_new_entry_multi_amount(self, app, spreadsheet):
        """Test that space-separated amounts in the input fail to parse (known bug)."""
        async with app.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app, "sheet", "mono user")
            await menu_select(pilot, app, "month", "janvier")
            await menu_select(pilot, app, "category", "out-foo")
            app.screen.query_one("#amount", Input).value = "15 20"
            await self.validate(pilot)
        self.assert_cell(
            spreadsheet,
            "mono user",
            "janvier",
            "out-foo",
            "=15 + 20",
        )

    async def test_tui_fetched_val_updates_after_confirm_spent(self, app, spreadsheet):
        """Test FetchedVals update after confirming a new expense entry."""
        async with app.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app, "sheet", "mono user")
            await menu_select(pilot, app, "month", "janvier")
            await menu_select(pilot, app, "category", "out-foo")

            TestTuiDisplayedValues.assert_all_fetched_val(app, "1234", "234", "-1000")

            await self.modify_input(pilot, "amount", "15")
            await self.validate(pilot)
            await pilot.pause()

            TestTuiDisplayedValues.assert_all_fetched_val(app, "1249", "234", "-1015")

    async def test_tui_fetched_val_updates_after_confirm_income(self, app, spreadsheet):
        """Test FetchedVals update after confirming a new income entry."""
        async with app.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app, "sheet", "mono user")
            await menu_select(pilot, app, "month", "fevrier")
            await menu_select(pilot, app, "category", "in-foo")

            TestTuiDisplayedValues.assert_all_fetched_val(app, "0", "111", "111")

            await self.modify_input(pilot, "amount", "50")
            await self.validate(pilot)
            await pilot.pause()

            TestTuiDisplayedValues.assert_all_fetched_val(app, "0", "161", "161")

    async def test_tui_fetched_val_updates_after_confirm_multiuser(self, app, spreadsheet):
        """Test FetchedVals update after confirming on a multiuser sheet."""
        async with app.run_test(size=(100, 50)) as pilot:
            await menu_select(pilot, app, "sheet", "multi users")
            await menu_select(pilot, app, "month", "janvier")
            await menu_select(pilot, app, "user", "alice")
            await menu_select(pilot, app, "category", "out-foo")

            TestTuiDisplayedValues.assert_all_fetched_val(app, "100", "150", "50")

            await self.modify_input(pilot, "amount", "25")
            await self.validate(pilot)
            await pilot.pause()

            TestTuiDisplayedValues.assert_all_fetched_val(app, "125", "150", "25")
