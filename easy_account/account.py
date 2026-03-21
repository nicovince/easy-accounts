"""Manage Account Spreadsheet."""

import openpyxl


class AccountSpreadsheet:
    """Class to manage an account spreadsheet."""

    def __init__(self, spreadsheet_path: str):
        self.path = spreadsheet_path
        self.wb = openpyxl.load_workbook(self.path)
        self.category_column = "A"

    def get_row_from_category(self, category: str):
        """Get the row for a matching category."""
        ws = self.wb.active
        categories = ws[self.category_column]
        for cell in categories:
            if cell.value == category:
                return cell.row
        assert False, f"{category} not found in {self.path}"
