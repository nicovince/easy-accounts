"""Manage spreadsheet"""

import openpyxl
from openpyxl.formula import Tokenizer


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

    @staticmethod
    def from_str(s: str):
        if s.isdecimal():
            return int(s)
        return float(s)

    def evaluate(self, sheet_name: str, col: str, row: int):
        cell_val = self.get_sheet(sheet_name)[f"{col}{row}"].value
        tokens = Tokenizer(cell_val)
        if len(tokens.items) == 1:
            return self.from_str(tokens.items[0].value)

        op = ""
        for t in tokens.items:
            if (t.type, t.subtype) == ("OPERAND", "NUMBER"):
                op += f"{t.value}"
            elif (t.type, t.subtype) == ("OPERATOR-INFIX", ""):
                op += f"{t.value}"
        return eval(op)
