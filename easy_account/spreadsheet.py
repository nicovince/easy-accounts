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
    OPERATOR_PRECEDENCE = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2,
    }

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

    @classmethod
    def _infix_to_postfix(cls, tokens):
        output = []
        operators = []
        i = 0
        func_arg_counts = []
        while i < len(tokens):
            t = tokens[i]
            if (t.type, t.subtype) == ("OPERAND", "NUMBER"):
                output.append(("number", cls.from_str(t.value)))
            elif (t.type, t.subtype) == ("OPERAND", "RANGE"):
                cell_range = CellRange(t.value)
                output.append(("range", cell_range))
            elif t.type == "FUNC" and t.subtype == "OPEN":
                operators.append(("func", t.value.upper()))
                func_arg_counts.append(1)
            elif t.type == "SEP":
                if func_arg_counts:
                    func_arg_counts[-1] += 1
            elif t.type == "OPERATOR-INFIX":
                while (
                    operators
                    and operators[-1][0] == "op"
                    and cls.OPERATOR_PRECEDENCE.get(operators[-1][1], 0)
                    >= cls.OPERATOR_PRECEDENCE.get(t.value, 0)
                ):
                    output.append(operators.pop())
                operators.append(("op", t.value))
            elif t.type == "PAREN" and t.value == "(":
                operators.append(("paren", "("))
            elif t.type == "FUNC" and t.subtype == "CLOSE":
                if operators and operators[-1][0] == "func":
                    func_token = operators.pop()
                    arg_count = func_arg_counts.pop() if func_arg_counts else 1
                    output.append(("func", func_token[1], arg_count))
            elif t.type == "PAREN" and t.value == ")":
                while operators and operators[-1] != ("paren", "("):
                    output.append(operators.pop())
                operators.pop()
                if operators and operators[-1][0] == "func":
                    func_token = operators.pop()
                    arg_count = func_arg_counts.pop() if func_arg_counts else 1
                    output.append(("func", func_token[1], arg_count))
            i += 1
        while operators:
            output.append(operators.pop())
        return output

    def _evaluate_postfix(self, postfix):
        stack = []
        for item in postfix:
            if item[0] == "number":
                stack.append(item[1])
            elif item[0] == "range":
                cell_range = item[1]
                if cell_range.is_single_cell():
                    cell = self.get_sheet(cell_range.get_parent_sheet_name())[
                        cell_range.get_start_pos()
                    ]
                    stack.append(self.evaluate(cell))
                else:
                    vals = self.evaluate_range(cell_range)
                    stack.append(sum(vals))
            elif item[0] == "func":
                arg_count = item[2] if len(item) > 2 else 1
                args = []
                for _ in range(arg_count):
                    args.append(stack.pop())
                args.reverse()
                if item[1] == "SUM(":
                    stack.append(sum(args))
                elif item[1] == "MAX(":
                    stack.append(max(args))
            elif item[0] == "op":
                b = stack.pop()
                a = stack.pop()
                if item[1] == "+":
                    stack.append(a + b)
                elif item[1] == "-":
                    stack.append(a - b)
                elif item[1] == "*":
                    stack.append(a * b)
                elif item[1] == "/":
                    stack.append(a / b)
        return stack[0] if stack else 0

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
        if cell_val is None:
            return 0
        if isinstance(cell_val, (int, float)):
            return cell_val
        if not isinstance(cell_val, str) or not cell_val.startswith("="):
            if isinstance(cell_val, str):
                try:
                    return self.from_str(cell_val)
                except ValueError:
                    return 0
            return 0
        tokens = Tokenizer(cell_val)
        postfix = self._infix_to_postfix(tokens.items)
        return self._evaluate_postfix(postfix)
