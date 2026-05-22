from textual.app import App, ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Button, Footer, Header, Input, Static, Select
from textual.screen import Screen
from textual.widget import Widget
import textual
import easy_account.config as ea_config
import importlib.metadata
import argparse
import easy_account.infomaniak
from easy_account.infomaniak import InfomaniakApi
from easy_account.account import AccountSpreadsheet


class Buttons(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Button("Pull", id="pull", classes="box")
        yield Button("Save", id="save", classes="box")
        yield Button("Push", id="push", classes="box")

    @textual.on(Button.Pressed, "#pull")
    def pull_file(self) -> None:
        """Action executed on pull."""
        config = easy_account.config.load_config(self.app.args.config)
        api_url = easy_account.config.get_kdrive_api_url(config)
        assert api_url is not None
        self.app.args.spreadsheet = easy_account.infomaniak.pull_file(api_url)
        self.app.account = AccountSpreadsheet(self.app.args.spreadsheet)
        self.screen.update_sheet_selection()


class CellSelector(Widget):
    DEFAULT_CSS = """
    CellSelector {
        height: auto;
        width: auto;
        layout: vertical;
    }
    """

    def __init__(self, prompt: str, identifier: str):
        self.prompt = prompt
        self.identifier = identifier
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Select(
            options=[],
            allow_blank=True,
            prompt=self.prompt,
            id=self.identifier,
            disabled=True,
            classes="box",
        )


class SelectionsCell(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield CellSelector("Sheet", "sheet")
        yield CellSelector("Month", "month")
        yield CellSelector("Category", "category")
        yield CellSelector("User", "user")

    def update_options(self, name: str, options: list | None):
        select = self.query_one(f"#{name}", Select)
        if options:
            select.disabled = False
            select.set_options([(opt, opt) for opt in options])
        else:
            select.disabled = True
            select.clear()

    def update_static(self, name: str, value: str) -> None:
        """Update the value of a Static."""
        static = self.app.screen.query_one(f"#{name}")
        static.update(value)

    @textual.on(Select.Changed, "#sheet")
    def update_menu_from_sheet(self, event):
        self.app.account.active_sheet = event.value
        self.update_options("month", self.app.account.get_spreadsheet_months())
        self.update_options("category", self.app.account.get_spreadsheet_categories())
        if self.app.account.is_multiuser():
            self.update_options("user", self.app.account.get_spreadsheet_users())
        else:
            self.update_options("user", None)

    @textual.on(Select.Changed, "#month")
    def update_fetched_vals_from_month(self, event):
        month = event.value
        try:
            config = easy_account.config.load_config(self.app.args.config)
        except easy_account.config.ConfigError:
            config = None

        tui_config = easy_account.config.get_tui_config(config)
        category_widget_links = (
            ("spent_value", tui_config["total_spent_category"]),
            ("income_value", tui_config["total_income_category"]),
            ("balance", tui_config["balance_category"]),
        )
        for widget_name, category in category_widget_links:
            if category and not self.app.account.is_multiuser():
                cell = self.app.account.get_cell(month, category)
                val = self.app.account.evaluate(cell)
            else:
                val = "N/A"
            self.update_static(widget_name, str(val))


class TextInputs(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Amount")
        yield Input(placeholder="Comment")


class FetchedVals(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Static("Spent")
        yield Static("15", id="spent_value", classes="value")
        yield Static("Income")
        yield Static("6", id="income_value", classes="value")
        yield Static("Balance")
        yield Static("1", id="balance", classes="value")


class MainScreen(Screen):
    """Main Screen for EasyAccount Text User Interface."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Buttons(id="buttons", classes="box")
        yield SelectionsCell(id="sidebar", classes="box")
        yield TextInputs(id="user-inputs", classes="box")
        yield FetchedVals(id="fetched-vals", classes="box")
        yield Footer(show_command_palette=True)

    def update_sheet_selection(self) -> None:
        if self.app.account is not None:
            sheet_sel = self.query_one("#sheet", Select)
            sheet_sel.disabled = False
            sheets_opts = [(s, s) for s in self.app.account.wb.sheetnames]
            sheet_sel.set_options(sheets_opts)

    def on_mount(self) -> None:
        self.update_sheet_selection()


class EasyAccountTUI(App):
    """A Textual app to manage EasyAccount."""

    CSS_PATH = "easy-account-tui.tcss"
    SUB_TITLE = importlib.metadata.version("easy-account")
    MODES = {
        "main": MainScreen,
    }

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(
            prog="easy-account-tui",
            description="Fill banking accounts spreadsheet from Text User Interface",
        )

        parser.add_argument(
            "-c",
            "--config",
            type=str,
            help=f"Path to an alternative config file to {ea_config.DEFAULT_CFG_FILE}",
            default=ea_config.DEFAULT_CFG_FILE,
        )

        parser.add_argument(
            "-f",
            "--spreadsheet",
            type=str,
            help="Path to spreadsheet to edit",
        )

        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {importlib.metadata.version('easy-account')}",
        )
        return parser.parse_args()

    def __init__(self) -> None:
        self.account = None
        self.args = self.parse_args()
        if self.args.spreadsheet:
            self.account = AccountSpreadsheet(self.args.spreadsheet)

        try:
            self.api = InfomaniakApi()
        except easy_account.infomaniak.MissingTokenError:
            self.api = InfomaniakApi("DUMMY_TOKEN")
        super().__init__()

    def on_mount(self) -> None:
        self.switch_mode("main")


def main():
    app = EasyAccountTUI()
    app.run()


if __name__ == "__main__":
    main()
