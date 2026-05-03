from textual.app import App, ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Button, Footer, Header, Input, Static, Select
from textual.screen import Screen
import easy_account.config as ea_config
import importlib.metadata
import argparse
import easy_account.infomaniak
from easy_account.infomaniak import InfomaniakApi


class Buttons(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Button("Pull", id="pull", classes="box")
        yield Button("Save", id="save", classes="box")
        yield Button("Push", id="push", classes="box")


class SelectionsCell(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Select(options=[], allow_blank=True, prompt="Sheet", disabled=True, id="sheet")
        yield Button("Month\n(-)", id="month")
        yield Button("Category\n(-)", id="category")
        yield Button("User\n(-)", id="user")


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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sheet":
            # Find the widget by ID and update its content
            display = self.query_one("#spent_value", Static)
            display.update("555")
            # You can also change styles dynamically
            display.styles.color = "green"
        elif event.button.id == "pull":
            config = easy_account.config.load_config(self.app.args.config)
            api_url = easy_account.config.get_kdrive_api_url(config)
            assert api_url is not None
            self.app.args.spreadsheet = easy_account.infomaniak.pull_file(api_url)
            sheet_sel = self.query_one("#sheet", Select)
            sheet_sel.disabled = False


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
        self.args = self.parse_args()
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
