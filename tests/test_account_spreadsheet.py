from easy_account.account import AccountSpreadsheet
import pytest


@pytest.fixture
def dummy_account():
    return AccountSpreadsheet("tests/dummy_account.xlsx")


def test_constructor():
    AccountSpreadsheet("tests/dummy_account.xlsx")


def test_account_get_row_from_category(dummy_account):
    cell = dummy_account.get_cell_category("foo")
    assert cell.row == 2


def test_account_invalid_category(dummy_account):
    with pytest.raises(AssertionError):
        dummy_account.get_cell_category("dsmfkj")
