"""Manage Account Spreadsheet."""

import openpyxl
from openpyxl.cell.cell import Cell


class AccountSpreadsheet:
    """Class to manage an account spreadsheet."""

    def __init__(self, spreadsheet_path: str):
        self.path = spreadsheet_path
        self.wb = openpyxl.load_workbook(self.path)
        self.category_column = "A"
        self.month_row = 1

    def get_cell_category(self, category: str) -> Cell:
        """Get the cell for a matching category."""
        ws = self.wb.active
        categories = ws[self.category_column]
        for cell in categories:
            if cell.value == category:
                return cell
        assert False, f"{category} not found in {self.path}"

    def get_cell_month(self, month: str) -> Cell:
        """Return the cell for a matching month."""
        ws = self.wb.active
        months = ws[self.month_row]
        for cell in months:
            if cell.value == month:
                return cell
        assert False, f"{month} not found in {self.path}"
