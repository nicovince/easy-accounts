import sys
import os
from pathlib import Path
from openpyxl import Workbook

import pytest

# Add the project root to the Python path so pytest can find the local modules
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Change working directory to project root for relative imports
os.chdir(project_root)


def fill_monouser_sheet(ws):
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
    col_month_offset = 2
    row_category_offset = 2
    categories = ["foo", "bar"]
    for idx, month in enumerate(months):
        ws.cell(row=1, column=(col_month_offset + idx), value=month)

    for idx, category in enumerate(categories):
        ws.cell(row=(row_category_offset + idx), column=1, value=category)


def fill_multiuser_sheet(ws):
    users = ["alice", "bob", "shared"]
    categories = ["foo", "bar"]
    col_month_offset = 2
    row_category_offset = 3
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
    for idx, month in enumerate(months):
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


@pytest.fixture(scope="session")
def monouser_account(tmp_path_factory):
    wb = Workbook()
    ws = wb.active
    fill_monouser_sheet(ws)
    path = f"{tmp_path_factory.mktemp('monoaccount')}/simple_mono_account.xlsx"
    wb.save(path)
    return path


@pytest.fixture
def fresh_monouser_account(tmp_path):
    """Create a fresh monouser spreadsheet for each test."""
    wb = Workbook()
    ws = wb.active
    fill_monouser_sheet(ws)
    path = tmp_path / "fresh_monouser_account.xlsx"
    wb.save(path)
    return str(path)


@pytest.fixture
def fresh_multiuser_account(tmp_path):
    """Create a fresh multiuser spreadsheet for each test."""
    wb = Workbook()
    ws = wb.active
    fill_multiuser_sheet(ws)
    path = tmp_path / "fresh_multiuser_account.xlsx"
    wb.save(path)
    return str(path)


@pytest.fixture(scope="session")
def multiuser_account_fixture(tmp_path_factory):
    wb = Workbook()
    ws = wb.active
    fill_multiuser_sheet(ws)
    path = f"{tmp_path_factory.mktemp('multiuser')}/multi_user_account.xlsx"
    wb.save(path)
    return path
