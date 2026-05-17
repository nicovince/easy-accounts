from easy_account.account import AccountSpreadsheet
import pytest


@pytest.fixture
def mono_account(spreadsheet):
    acc = AccountSpreadsheet(spreadsheet)
    acc.active_sheet = "mono user"
    return acc


@pytest.fixture
def multi_account(spreadsheet):
    acc = AccountSpreadsheet(spreadsheet)
    acc.active_sheet = "multi users"
    return acc


def test_account_constructor():
    AccountSpreadsheet("tests/dummy_account.xlsx")


def test_account_get_row_from_category(mono_account):
    cell = mono_account.get_cell_category("out-foo")
    assert cell.row == 2


def test_account_invalid_category(mono_account):
    with pytest.raises(AssertionError):
        mono_account.get_cell_category("dsmfkj")


def test_account_get_cell_month(mono_account):
    cell = mono_account.get_cell_month("janvier")
    assert cell.column_letter == "B"


def test_account_get_cell_month_invalid(mono_account):
    with pytest.raises(AssertionError):
        mono_account.get_cell_month("qmlfkj")


def test_account_get_cell_month_category(mono_account):
    c = mono_account.get_cell(month="janvier", category="out-foo")
    assert c.coordinate == "B2"


def test_account_get_cell_month_category_invalid_month(mono_account):
    with pytest.raises(AssertionError):
        mono_account.get_cell(month="pwet", category="out-foo")


def test_account_get_cell_month_category_invalid_category(mono_account):
    with pytest.raises(AssertionError):
        mono_account.get_cell(month="janvier", category="pwet")


def test_account_multi_get_month(multi_account):
    c = multi_account.get_cell_month("janvier")
    assert c.column_letter == "B"
    c = multi_account.get_cell_month("fevrier")
    assert c.column_letter == "E"
    c = multi_account.get_cell_month("decembre")
    assert c.column_letter == "AF"


def test_account_multi_next_month(multi_account):
    c = multi_account.get_cell_month("janvier")
    cn = multi_account.get_next_month_cell(c)
    assert cn.column_letter == "E"
    c = multi_account.get_cell_month("decembre")
    cn = multi_account.get_next_month_cell(c)
    assert cn.column_letter == "AI"


def test_account_multi_get_cell_month_category_user(multi_account):
    c = multi_account.get_cell(month="janvier", category="out-foo", user="alice")
    assert c.coordinate == "B3"
    c = multi_account.get_cell(month="janvier", category="out-foo", user="bob")
    assert c.coordinate == "C3"
    c = multi_account.get_cell(month="janvier", category="out-foo", user="shared")
    assert c.coordinate == "D3"

    c = multi_account.get_cell(month="decembre", category="out-foo", user="alice")
    assert c.coordinate == "AF3"
    c = multi_account.get_cell(month="decembre", category="out-foo", user="bob")
    assert c.coordinate == "AG3"
    c = multi_account.get_cell(month="decembre", category="out-foo", user="shared")
    assert c.coordinate == "AH3"


def test_account_multisheet_valid_sheet(multi_account):
    c = multi_account.get_cell(month="janvier", category="out-foo", user="alice")
    assert c.coordinate == "B3"


def test_account_multisheet_invalid_sheet(mono_account):
    with pytest.raises(AssertionError):
        mono_account.active_sheet = "invalid"


def test_account_add_entry(multi_account):
    c = multi_account.get_cell(month="janvier", category="out-foo")
    multi_account.add_entry("janvier", "out-foo", 3.14, "pi")
    assert c.value == "=3.14"
    assert c.comment.text == "pi"
    multi_account.add_entry("janvier", "out-foo", 3.14, "pi")
    assert c.value == "=3.14 + 3.14"
    assert c.comment.text == "pi\npi"
    c = multi_account.get_cell(month="fevrier", category="out-foo")
    multi_account.add_entry("fevrier", "out-foo", 3615)
    assert c.value == "=3615"
    assert c.comment is None


def test_account_add_entry_with_list_empty_cell(mono_account):
    """Test adding a list of floats to an empty cell."""
    c = mono_account.get_cell(month="janvier", category="out-foo")
    mono_account.add_entry("janvier", "out-foo", [1.0, 2.0, 3.0])
    assert c.value == "=1.0 + 2.0 + 3.0"
    assert c.comment is None


def test_account_add_entry_with_list_existing_cell(mono_account):
    """Test adding a list of floats to an existing cell."""
    c = mono_account.get_cell(month="mars", category="out-foo")
    mono_account.add_entry("mars", "out-foo", [1.0, 2.0])
    assert c.value == "=1.0 + 2.0"
    mono_account.add_entry("mars", "out-foo", [3.0, 4.0])
    assert c.value == "=1.0 + 2.0 + 3.0 + 4.0"


def test_account_add_entry_with_list_and_comment(mono_account):
    """Test adding a list of floats with a comment."""
    c = mono_account.get_cell(month="avril", category="out-foo")
    mono_account.add_entry("avril", "out-foo", [5.5, 4.5], "mixed")
    assert c.value == "=5.5 + 4.5"
    assert c.comment.text == "mixed"


def test_account_add_entry_with_single_float_in_list(mono_account):
    """Test adding a single float in a list."""
    c = mono_account.get_cell(month="mai", category="out-foo")
    mono_account.add_entry("mai", "out-foo", [10.0])
    assert c.value == "=10.0"


class TestAccountSpreadsheetHelpers:
    """Tests for AccountSpreadsheet helper methods."""

    def test_get_spreadsheet_months_monouser(self, mono_account):
        """Test getting months from monouser spreadsheet."""
        months = mono_account.get_spreadsheet_months()
        assert "janvier" in months
        assert "decembre" in months
        assert len(months) == 11

    def test_get_spreadsheet_months_multiuser(self, multi_account):
        """Test getting months from multiuser spreadsheet."""
        months = multi_account.get_spreadsheet_months()
        assert "janvier" in months
        assert "decembre" in months
        assert len(months) == 11

    def test_get_spreadsheet_categories(self, mono_account):
        """Test getting categories from spreadsheet."""
        categories = mono_account.get_spreadsheet_categories()
        assert "out-foo" in categories
        assert "out-bar" in categories

    def test_get_spreadsheet_users_monouser(self, mono_account):
        """Test that monouser spreadsheet returns empty user list."""
        users = mono_account.get_spreadsheet_users()
        assert users == []

    def test_get_spreadsheet_users_multiuser(self, multi_account):
        """Test getting users from multiuser spreadsheet."""
        users = multi_account.get_spreadsheet_users()
        assert ["alice", "bob", "shared"] == users
        assert "alice" in users
        assert "bob" in users
        assert "shared" in users

    def test_is_multiuser_monouser(self, mono_account):
        """Test that monouser spreadsheet is correctly identified."""
        assert mono_account.is_multiuser() is False

    def test_is_multiuser_multiuser(self, multi_account):
        """Test that multiuser spreadsheet is correctly identified."""
        assert multi_account.is_multiuser() is True
