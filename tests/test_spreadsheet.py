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


def test_spreadsheet_get_sheet_by_name(sample_spreadsheet):
    ws = sample_spreadsheet.get_sheet("Sheet1")
    assert ws.title == "Sheet1"


def test_spreadsheet_get_cell_value(sample_spreadsheet):
    ws = sample_spreadsheet.get_sheet("Sheet1")
    ws["A1"] = 5
    val = sample_spreadsheet.get_cell_value("Sheet1", "A", 1)
    assert val == 5


def test_spreadsheet_evaluate_no_formula_int(sample_spreadsheet):
    ws = sample_spreadsheet.get_sheet("Sheet1")
    ws["A1"] = "5"
    val = sample_spreadsheet.evaluate("Sheet1", "A", 1)
    assert val == 5
