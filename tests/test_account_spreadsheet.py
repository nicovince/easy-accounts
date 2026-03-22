from easy_account.account import AccountSpreadsheet
from openpyxl import Workbook
import pytest


@pytest.fixture(scope="session")
def generated_account(tmp_path_factory):
    months = [
        "janvier",
        "fevrier",
        "mars",
        "avril",
        "mai",
        "juin",
        "aout",
        "septembre",
        "octobre",
        "novembre",
        "decembre",
    ]
    categories = ["foo", "bar"]
    wb = Workbook()
    ws = wb.active
    col_month_offset = 2
    row_category_offset = 2
    for idx, month in enumerate(months):
        ws.cell(row=1, column=(col_month_offset + idx), value=month)

    for idx, category in enumerate(categories):
        ws.cell(row=(row_category_offset + idx), column=1, value=category)

    path = f"{tmp_path_factory.mktemp('data')}/simple_mono_account.xlsx"
    wb.save(path)
    return path


@pytest.fixture
def dummy_account(generated_account):
    return AccountSpreadsheet(generated_account)


def test_account_constructor():
    AccountSpreadsheet("tests/dummy_account.xlsx")


def test_account_get_row_from_category(dummy_account):
    cell = dummy_account.get_cell_category("foo")
    assert cell.row == 2


def test_account_invalid_category(dummy_account):
    with pytest.raises(AssertionError):
        dummy_account.get_cell_category("dsmfkj")


def test_account_get_cell_month(dummy_account):
    cell = dummy_account.get_cell_month("janvier")
    assert cell.column_letter == "B"


def test_account_get_cell_month_invalid(dummy_account):
    with pytest.raises(AssertionError):
        dummy_account.get_cell_month("qmlfkj")


def test_account_get_cell_month_category(dummy_account):
    c = dummy_account.get_cell(month="janvier", category="foo")
    assert c.coordinate == "B2"


def test_account_get_cell_month_category_invalid_month(dummy_account):
    with pytest.raises(AssertionError):
        dummy_account.get_cell(month="pwet", category="foo")


def test_account_get_cell_month_category_invalid_category(dummy_account):
    with pytest.raises(AssertionError):
        dummy_account.get_cell(month="janvier", category="pwet")
