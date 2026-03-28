"""Tests for CLI module."""

import os
import sys

import pytest

from easy_account.config import create_example_config


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
        self, tmp_path_cwd, monouser_account, capsys, monkeypatch
    ):
        """Test that invalid --user returns error when config file exists."""
        from easy_account.cli import main

        config_path = tmp_path_cwd / ".easy-account.toml"
        create_example_config(config_path)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                str(monouser_account),
                "Sheet",
                "janvier",
                "foo",
                "100",
                "--user",
                "invalid_user",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "invalid_user" in captured.err

    def test_invalid_user_without_config_returns_error(
        self, tmp_path_cwd, multiuser_account_fixture, capsys, monkeypatch
    ):
        """Test that invalid --user returns error when config file does not exist."""
        from easy_account.cli import main

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                str(multiuser_account_fixture),
                "Sheet",
                "janvier",
                "foo",
                "100",
                "--user",
                "invalid_user",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "invalid_user" in captured.err
        assert "not found in spreadsheet" in captured.err

    def test_valid_user_without_config_no_error(
        self, tmp_path_cwd, multiuser_account_fixture, capsys, monkeypatch
    ):
        """Test that valid --user does not return error when config file does not exist."""
        from easy_account.cli import main

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                str(multiuser_account_fixture),
                "Sheet",
                "janvier",
                "foo",
                "100",
                "--user",
                "alice",
            ],
        )

        main()

        captured = capsys.readouterr()
        assert "alice" not in captured.err

    def test_user_ignored_when_spreadsheet_is_monouser(
        self, tmp_path_cwd, monouser_account, capsys, monkeypatch
    ):
        """Test that --user is accepted for monouser spreadsheet without config."""
        from easy_account.cli import main

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                str(monouser_account),
                "Sheet",
                "janvier",
                "foo",
                "100",
                "--user",
                "any_user",
            ],
        )

        main()

        captured = capsys.readouterr()
        assert "any_user" not in captured.err
