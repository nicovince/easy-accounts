"""Manage spreadsheet"""

import openpyxl


class Spreadsheet:
    def __init__(self, spreadsheet_path: str):
        self.path = spreadsheet_path
        self.wb = openpyxl.load_workbook(self.path)

    @property
    def active_sheet(self):
        return self._active_sheet

    @active_sheet.setter
    def active_sheet(self, value):
        assert value in self.wb.sheetnames
        self._active_sheet = value

    def save(self):
        """Save file to disk."""
        self.wb.save(self.path)

    def get_sheet(self, sheet_name: str = None):
        """Get the requested sheet."""
        if sheet_name is not None:
            return self.wb[sheet_name]
        if self.active_sheet is None:
            return self.wb.active
        return self.wb[self.active_sheet]

    def get_cell_value(self, sheet_name: str, col: str, row: int):
        return self.get_sheet(sheet_name)[f"{col}{row}"].value
