"""Manage spreadsheet"""

import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.cell.cell import Cell
import re


class CellRange:
    def __init__(self, cell_range: str):
        cell_range_re = re.compile(r"((\w*)!)?([A-Z]+)([0-9]+):?(([A-Z]+)([0-9]+))?")
        m = cell_range_re.match(cell_range)
        self.sheet_name = m.group(2)
        self.start_col = m.group(3)
        self.start_row = m.group(4)
        self.end_col = m.group(6)
        self.end_row = m.group(7)

    def get_parent_sheet_name(self):
        return self.sheet_name

    def is_single_cell(self):
        return self.end_col is None

    def get_start_pos(self):
        return f"{self.start_col}{self.start_row}"

    def get_end_pos(self):
        assert not self.is_single_cell()
        return f"{self.end_col}{self.end_row}"

    def get_range(self):
        assert not self.is_single_cell()
        return f"{self.get_start_pos()}:{self.get_end_pos()}"


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

    def evaluate_range(self, cell_range: CellRange) -> list:
        cell_range_eval = list()
        for row in self.get_sheet(cell_range.get_parent_sheet_name())[cell_range.get_range()]:
            for cell in row:
                cell_range_eval.append(self.evaluate(cell))
        return cell_range_eval

    def evaluate(self, cell: Cell):
        cell_val = cell.value
        tokens = Tokenizer(cell_val)
        op = ""
        for t in tokens.items:
            if self.is_token_simple(t):
                op += f"{t.value}"
            elif (t.type, t.subtype) == ("OPERAND", "RANGE"):
                cell_range = CellRange(t.value)
                if cell_range.is_single_cell():
                    cell = self.get_sheet(cell_range.get_parent_sheet_name())[
                        cell_range.get_start_pos()
                    ]
                    op += str(self.evaluate(cell))
                else:
                    cell_range_vals = self.evaluate_range(cell_range)
                    # assume SUM
                    s = 0
                    for v in cell_range_vals:
                        s += v
                    op += str(s)

        return eval(op)
