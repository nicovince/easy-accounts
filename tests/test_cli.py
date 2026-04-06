"""Tests for CLI module."""

import os
import sys

import pytest

from easy_account.config import create_example_config
import easy_account.cli


@pytest.fixture
def tmp_path_cwd(tmp_path):
    """Set current working directory to tmp_path and restore on teardown"""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


class TestCliUserValidation:
    """Tests for CLI user validation."""

    def test_invalid_user_with_config_returns_error(
        self, tmp_path_cwd, spreadsheet, capsys, monkeypatch
    ):
        """Test that invalid --user returns error when config file exists."""

        config_path = tmp_path_cwd / ".easy-account.toml"
        create_example_config(config_path)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "foo",
                "100",
                "--user",
                "invalid_user",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "invalid_user" in captured.err

    def test_invalid_user_without_config_returns_error(
        self, tmp_path_cwd, spreadsheet, capsys, monkeypatch
    ):
        """Test that invalid --user returns error when config file does not exist."""

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "multi users",
                "janvier",
                "foo",
                "100",
                "--user",
                "invalid_user",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "invalid_user" in captured.err
        assert "not found in spreadsheet" in captured.err

    def test_valid_user_without_config_no_error(
        self, tmp_path_cwd, spreadsheet, capsys, monkeypatch
    ):
        """Test that valid --user does not return error when config file does not exist."""

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "multi users",
                "janvier",
                "foo",
                "100",
                "--user",
                "alice",
            ],
        )

        easy_account.cli.main()

        captured = capsys.readouterr()
        assert "alice" not in captured.err

    def test_user_ignored_when_spreadsheet_is_monouser(
        self, tmp_path_cwd, spreadsheet, capsys, monkeypatch
    ):
        """Test that --user is accepted for monouser spreadsheet without config."""

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "foo",
                "100",
                "--user",
                "any_user",
            ],
        )

        easy_account.cli.main()

        captured = capsys.readouterr()
        assert "any_user" not in captured.err


class TestCliInsertCmd:
    """Tests for CLI insert command."""

    def test_mono_account_show_only(self, spreadsheet_unmodified, capsys, monkeypatch):
        """Test that --show-only report a value."""

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet_unmodified),
                "mono user",
                "janvier",
                "bar",
                "100",
                "--show-only",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1234" in captured.out

    def test_multi_account_show_only(self, spreadsheet_unmodified, capsys, monkeypatch):
        """Test that --show-only report a value."""

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet_unmodified),
                "multi users",
                "janvier",
                "bar",
                "100",
                "--user",
                "bob",
                "--show-only",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "4321" in captured.out
