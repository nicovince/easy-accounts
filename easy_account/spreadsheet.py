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

    def get_sheet(self):
        """Get the requested sheet."""
        if self.active_sheet is None:
            return self.wb.active
        return self.wb[self.active_sheet]
