"""Manage spreadsheet"""

import openpyxl
from openpyxl.formula import Tokenizer
import re


class Spreadsheet:
    def __init__(self, spreadsheet_path: str):
        self.path = spreadsheet_path
        self.wb = openpyxl.load_workbook(self.path)
        self._active_sheet = None

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

    @staticmethod
    def is_token_simple(token):
        return (
            (token.type, token.subtype) == ("OPERAND", "NUMBER")
            or (token.type, token.subtype) == ("OPERATOR-INFIX", "")
            or (token.type, token.subtype) == ("LITERAL", "")
            or False
        )

    @staticmethod
    def split_cell_ref(cell_ref: str):
        m = re.match(r"((\w*)!)?([A-Z]+)([0-9]+)", cell_ref)
        ref = (m.group(2), m.group(3), m.group(4))
        return ref

    def evaluate(self, sheet_name: str, col: str, row: int):
        cell_val = self.get_sheet(sheet_name)[f"{col}{row}"].value
        tokens = Tokenizer(cell_val)
        op = ""
        for t in tokens.items:
            if self.is_token_simple(t):
                op += f"{t.value}"
            elif (t.type, t.subtype) == ("OPERAND", "RANGE"):
                cell_ref = self.split_cell_ref(t.value)
                op += str(self.evaluate(cell_ref[0], cell_ref[1], cell_ref[2]))
        return eval(op)
