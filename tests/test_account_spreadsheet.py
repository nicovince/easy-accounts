from easy_account.account import AccountSpreadsheet
from openpyxl import Workbook
import pytest


def get_months():
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
    return months


@pytest.fixture(scope="session")
def monouser_account(tmp_path_factory):
    categories = ["foo", "bar"]
    wb = Workbook()
    ws = wb.active
    col_month_offset = 2
    row_category_offset = 2
    for idx, month in enumerate(get_months()):
        ws.cell(row=1, column=(col_month_offset + idx), value=month)

    for idx, category in enumerate(categories):
        ws.cell(row=(row_category_offset + idx), column=1, value=category)

    path = f"{tmp_path_factory.mktemp('data')}/simple_mono_account.xlsx"
    wb.save(path)
    return path


@pytest.fixture(scope="session")
def multiuser_account(tmp_path_factory):
    users = ["alice", "bob", "shared"]
    categories = ["foo", "bar"]
    wb = Workbook()
    ws = wb.active
    col_month_offset = 2
    row_category_offset = 3

    for idx, month in enumerate(get_months()):
        month_start_col = col_month_offset + idx * len(users)
        month_end_col = col_month_offset + (idx + 1) * len(users) - 1
        ws.cell(row=1, column=month_start_col, value=month)
        ws.merge_cells(
            start_row=1, start_column=month_start_col, end_row=1, end_column=month_end_col
        )
        for user_idx, user in enumerate(users):
            ws.cell(row=2, column=(col_month_offset + idx * len(users) + user_idx), value=user)

    for idx, category in enumerate(categories):
        ws.cell(row=(row_category_offset + idx), column=1, value=category)

    path = f"{tmp_path_factory.mktemp('data')}/multi_user_account.xlsx"
    wb.save(path)
    return AccountSpreadsheet(path)


@pytest.fixture
def dummy_account(monouser_account):
    return AccountSpreadsheet(monouser_account)


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


def test_account_multi_get_month(multiuser_account):
    c = multiuser_account.get_cell_month("janvier")
    assert c.column_letter == "B"
    c = multiuser_account.get_cell_month("fevrier")
    assert c.column_letter == "E"
    c = multiuser_account.get_cell_month("decembre")
    assert c.column_letter == "AF"


def test_account_multi_next_month(multiuser_account):
    c = multiuser_account.get_cell_month("janvier")
    cn = multiuser_account.get_next_month_cell(c)
    assert cn.column_letter == "E"
    c = multiuser_account.get_cell_month("decembre")
    cn = multiuser_account.get_next_month_cell(c)
    assert cn.column_letter == "AI"
