import pytest
from openpyxl import Workbook
from easy_account.spreadsheet import Spreadsheet


@pytest.fixture(scope="session")
def sample_spreadsheet(tmp_path_factory):
    path = f"{tmp_path_factory.mktemp('sample_spreadsheet')}/sample_spreadsheet.xlsx"
    wb = Workbook()
    ws = wb.active
    wb.remove(ws)
    wb.create_sheet("Sheet1")
    wb.create_sheet("Sheet2")
    wb.save(path)
    return Spreadsheet(path)


class TestSpreadsheetHelpers:
    """Test helpers from Spreadsheet"""

    def test_spreadsheet_get_sheet_by_name(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        assert ws.title == "Sheet1"

    def test_spreadsheet_get_cell_value(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = 5
        val = sample_spreadsheet.get_cell_value("Sheet1", "A", 1)
        assert val == 5

    @staticmethod
    def check_splitted_cell_ref(ref, sheet, col, row):
        res = Spreadsheet.split_cell_ref(ref)
        assert res == (sheet, col, row)

    def test_spreadsheet_split_cell_ref(self):
        self.check_splitted_cell_ref("A1", None, "A", "1")
        self.check_splitted_cell_ref("AA1", None, "AA", "1")
        self.check_splitted_cell_ref("AA12", None, "AA", "12")
        self.check_splitted_cell_ref("Sheet!AA12", "Sheet", "AA", "12")


class TestSpreadsheetEvaluate:
    """Test Spreadsheet Evaluation"""

    def test_spreadsheet_evaluate_no_formula_int(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "5"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
        assert val == 5

    def test_spreadsheet_evaluate_no_formula_float(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "5.2"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
        assert val == 5.2

    def test_spreadsheet_evaluate_formula_int(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "=3"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
        assert val == 3

    def test_spreadsheet_evaluate_formula_float(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "=3.14"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
        assert val == 3.14

    def test_spreadsheet_evaluate_formula_add_int(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "=5+3"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
        assert val == 8

    def test_spreadsheet_evaluate_formula_add_float(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "=0.1 + 3.4"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
        assert val == 3.5

    def test_spreadsheet_evaluate_cell_ref(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "5"
        ws["A2"] = "=A1"
        val = sample_spreadsheet.evaluate("Sheet1", "A", 2)
        assert val == 5

    def test_spreadsheet_evaluate_cell_ref_other_sheet(self, sample_spreadsheet):
        ws = sample_spreadsheet.get_sheet("Sheet1")
        ws["A1"] = "5"
        ws2 = sample_spreadsheet.get_sheet("Sheet2")
        ws2["A1"] = "=3 + Sheet1!A1"
        val = sample_spreadsheet.evaluate("Sheet2", "A", 1)
        assert val == 8
