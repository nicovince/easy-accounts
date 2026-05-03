from textual.app import App, ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Button, Footer, Header, Input, Static
import easy_account.config as ea_config
import importlib.metadata
import argparse


class Buttons(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Button("Pull", id="pull", classes="box")
        yield Button("Save", id="save", classes="box")
        yield Button("Push", id="push", classes="box")


class SelectionsCell(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Button("Sheet\n(-)", id="sheet")
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
        yield Static("5", id="spent_value")
        yield Static("Income")
        yield Static("6", id="income_value")
        yield Static("Balance")
        yield Static("1", id="balance")


class EasyAccountTUI(App):
    """A Textual app to manage EasyAccount."""

    CSS_PATH = "easy-account-tui.tcss"
    SUB_TITLE = importlib.metadata.version("easy-account")

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
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Buttons(id="buttons", classes="box")
        yield SelectionsCell(id="sidebar", classes="box")
        yield TextInputs(id="user-inputs", classes="box")
        yield FetchedVals(id="fetched-vals", classes="box")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sheet":
            # Find the widget by ID and update its content
            display = self.query_one("#spent_value", Static)
            display.update("555")
            # You can also change styles dynamically
            display.styles.color = "green"


if __name__ == "__main__":
    app = EasyAccountTUI()
    app.run()
