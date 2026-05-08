"""Tests for CLI module."""

import sys
import re
from unittest.mock import MagicMock, patch

import pytest

from easy_account.config import create_example_config
import easy_account.cli


class TestCli:
    @staticmethod
    def assert_show(stdout, value):
        """Assert that value is shown in stdout"""
        expect = rf"Show content of <.*>: {value}"
        assert re.search(expect, stdout), f"Expected '{value}' to be shown in output:\n{stdout}"


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
                "out-foo",
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

    def test_invalid_user_with_custom_config_returns_error(
        self, tmp_path_cwd, spreadsheet, capsys, monkeypatch
    ):
        """Test that invalid --user returns error when config file exists."""

        config_path = tmp_path_cwd / ".easy-account-custom.toml"
        create_example_config(config_path)
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[months]
months = ["janvier"]

[categories]
categories = ["out-foo"]

[users]
users = ["john", "jane", "jack"]
"""
        config_path.write_text(config_content)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "--config",
                ".easy-account-custom.toml",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-foo",
                "100",
                "--user",
                "john",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "john" in captured.err

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
                "out-foo",
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
                "out-foo",
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
                "out-foo",
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
                "out-bar",
                "100",
                "--show-only",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1234" in captured.out


class TestCliPullCmd:
    """Tests for CLI pull command."""

    def test_pull_no_api_url_error(self, tmp_path_cwd, capsys, monkeypatch):
        """Test that pull without API URL returns error."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        monkeypatch.setattr(
            sys,
            "argv",
            ["easy-account", "pull"],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No API URL provided" in captured.err

    def test_pull_invalid_api_url_error(self, tmp_path_cwd, capsys, monkeypatch):
        """Test that pull with invalid API URL returns error."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        monkeypatch.setattr(
            sys,
            "argv",
            ["easy-account", "pull", "invalid_url"],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid API URL format" in captured.err

    def test_pull_file_already_exists(self, tmp_path_cwd, capsys, monkeypatch):
        """Test successful pull command."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        test_file = tmp_path_cwd / "test.xlsx"
        test_file.write_bytes(b"test content")

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "pull",
                "https://api.infomaniak.com/2/drive/1475057/files/9",
            ],
        )

        mock_file_info = MagicMock()
        mock_file_info.name = str(test_file)

        with patch("easy_account.infomaniak.InfomaniakApi") as MockApi:
            mock_api = MagicMock()
            mock_api.get_file_info.return_value = mock_file_info
            MockApi.return_value = mock_api

            with pytest.raises(SystemExit) as exc_info:
                easy_account.cli.main()
            assert exc_info.value.code == 1

            mock_api.get_file_info.assert_called_once_with(1475057, 9)

        captured = capsys.readouterr()
        assert f"Error: File {test_file} already exists" in captured.err

    def test_pull_success(self, tmp_path_cwd, capsys, monkeypatch):
        """Test successful pull command."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        test_file = tmp_path_cwd / "test.xlsx"

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "pull",
                "https://api.infomaniak.com/2/drive/1475057/files/9",
            ],
        )

        mock_file_info = MagicMock()
        mock_file_info.name = str(test_file)

        with patch("easy_account.infomaniak.InfomaniakApi") as MockApi:
            mock_api = MagicMock()
            mock_api.get_file_info.return_value = mock_file_info
            mock_api.download_file.return_value = None
            MockApi.return_value = mock_api

            with pytest.raises(SystemExit) as exc_info:
                easy_account.cli.main()
            assert exc_info.value.code == 0

            mock_api.get_file_info.assert_called_once_with(1475057, 9)
            mock_api.download_file.assert_called_once()

        captured = capsys.readouterr()
        assert f"Downloaded: {test_file}" in captured.out


class TestCliPushCmd:
    """Tests for CLI push command."""

    def test_push_no_api_url_error(self, tmp_path_cwd, capsys, monkeypatch):
        """Test that push without API URL returns error."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        monkeypatch.setattr(
            sys,
            "argv",
            ["easy-account", "push"],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No API URL provided" in captured.err

    def test_push_invalid_api_url_error(self, tmp_path_cwd, capsys, monkeypatch):
        """Test that push with invalid API URL returns error."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        monkeypatch.setattr(
            sys,
            "argv",
            ["easy-account", "push", "invalid_url"],
        )

        with pytest.raises(SystemExit) as exc_info:
            easy_account.cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid API URL format" in captured.err

    def test_push_file_not_found_error(self, tmp_path_cwd, capsys, monkeypatch):
        """Test that push returns error when local file doesn't exist."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "push",
                "https://api.infomaniak.com/2/drive/1475057/files/9",
            ],
        )

        mock_file_info = MagicMock()
        mock_file_info.name = "test.xlsx"

        with patch("easy_account.cli.InfomaniakApi") as MockApi:
            mock_api = MagicMock()
            mock_api.get_file_info.return_value = mock_file_info
            MockApi.return_value = mock_api

            with pytest.raises(SystemExit) as exc_info:
                easy_account.cli.main()

            assert exc_info.value.code == 1
            mock_api.get_file_info.assert_called_once_with(1475057, 9)

        captured = capsys.readouterr()
        assert "Local file not found" in captured.err

    def test_push_success(self, tmp_path_cwd, capsys, monkeypatch):
        """Test successful push command."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        test_file = tmp_path_cwd / "test.xlsx"
        test_file.write_bytes(b"test content")

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "push",
                "https://api.infomaniak.com/2/drive/1475057/files/9",
            ],
        )

        mock_file_info = MagicMock()
        mock_file_info.name = "test.xlsx"

        with patch("easy_account.cli.InfomaniakApi") as MockApi:
            mock_api = MagicMock()
            mock_api.get_file_info.return_value = mock_file_info
            mock_api.upload_file.return_value = None
            MockApi.return_value = mock_api

            with pytest.raises(SystemExit) as exc_info:
                easy_account.cli.main()
            assert exc_info.value.code == 0

            mock_api.get_file_info.assert_called_once_with(1475057, 9)
            mock_api.upload_file.assert_called_once()

        captured = capsys.readouterr()
        assert "Uploaded: test.xlsx" in captured.out

    def test_push_with_api_url_from_config(self, tmp_path_cwd, capsys, monkeypatch):
        """Test push uses API URL from config when not provided as argument."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[kdrive]
api_url = "https://api.infomaniak.com/2/drive/1475057/files/9"
"""
        config_path.write_text(config_content)

        test_file = tmp_path_cwd / "test.xlsx"
        test_file.write_bytes(b"test content")

        monkeypatch.setattr(
            sys,
            "argv",
            ["easy-account", "push"],
        )

        mock_file_info = MagicMock()
        mock_file_info.name = "test.xlsx"

        with patch("easy_account.cli.InfomaniakApi") as MockApi:
            mock_api = MagicMock()
            mock_api.get_file_info.return_value = mock_file_info
            mock_api.upload_file.return_value = None
            MockApi.return_value = mock_api

            with pytest.raises(SystemExit) as exc_info:
                easy_account.cli.main()
            assert exc_info.value.code == 0

            mock_api.get_file_info.assert_called_once_with(1475057, 9)

        captured = capsys.readouterr()
        assert "Uploaded: test.xlsx" in captured.out


class TestCliDefaultReportFromConfig:
    """Tests for default report from config with omitted month."""

    def test_multi_account_report(self, spreadsheet, capsys, monkeypatch):
        """Test that --report show the cell value."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "multi users",
                "janvier",
                "out-bar",
                "100",
                "--user",
                "bob",
                "--report",
                "janvier,out-bar,bob",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "4421" in captured.out

    def test_default_report_from_config(self, spreadsheet, capsys, monkeypatch, tmp_path_cwd):
        """Test that default report from config is used when --report not specified."""
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[months]
months = ["janvier", "fevrier", "mars"]

[categories]
categories = ["out-foo", "out-bar"]

[report]
report = "janvier,out-bar"
"""
        config_path.write_text(config_content)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1334" in captured.out

    def test_cli_report_overrides_config_default(
        self, spreadsheet, capsys, monkeypatch, tmp_path_cwd
    ):
        """Test that explicit --report overrides config default."""
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[months]
months = ["janvier", "fevrier", "mars"]

[categories]
categories = ["out-foo", "out-bar"]

[report]
report = "janvier,out-foo"
"""
        config_path.write_text(config_content)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
                "--report",
                "janvier,out-bar",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1334" in captured.out

    def test_cli_report_with_category_only_uses_current_month(
        self, spreadsheet, capsys, monkeypatch
    ):
        """Test that --report with only category uses current month from args."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
                "--report",
                ",out-bar",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1334" in captured.out

    def test_cli_report_with_empty_month_uses_current_month(self, spreadsheet, capsys, monkeypatch):
        """Test that --report with empty month uses current month from args."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "fevrier",
                "out-bar",
                "100",
                "--report",
                ",out-bar",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "100.0" in captured.out

    def test_cli_report_with_user_and_empty_month_uses_current_month(
        self, spreadsheet, capsys, monkeypatch
    ):
        """Test that --report with empty month and user uses current month from args."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "multi users",
                "janvier",
                "out-bar",
                "100",
                "--user",
                "bob",
                "--report",
                ",out-bar,bob",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "4421" in captured.out

    def test_default_report_with_omitted_month_uses_current_month(
        self, spreadsheet, capsys, monkeypatch, tmp_path_cwd
    ):
        """Test that config report with omitted month uses current month from args."""
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[months]
months = ["janvier", "fevrier", "mars"]

[categories]
categories = ["out-foo", "out-bar"]

[report]
report = ",out-bar"
"""
        config_path.write_text(config_content)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1334" in captured.out


class TestCliShowCmd(TestCli):
    """Tests for CLI show command."""

    def test_show_mono_account(self, spreadsheet_unmodified, capsys, monkeypatch):
        """Test show command for mono account."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "show",
                str(spreadsheet_unmodified),
                "mono user",
                "janvier",
                "out-bar",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "1234" in captured.out

    def test_show_multi_account(self, spreadsheet_unmodified, capsys, monkeypatch):
        """Test that --show-only report a value."""

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "show",
                str(spreadsheet_unmodified),
                "multi users",
                "janvier",
                "out-bar",
                "--user",
                "bob",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        assert "4321" in captured.out

    def test_cli_multiple_reports_from_cli(self, spreadsheet, capsys, monkeypatch):
        """Test that multiple --report values work from CLI."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
                "--report",
                "janvier,out-foo",
                "janvier,out-bar",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        # out-foo has value 0, out-bar has value 1334 in test spreadsheet
        self.assert_show(captured.out, 0)
        self.assert_show(captured.out, 1334)

    def test_cli_multiple_reports_from_config(self, spreadsheet, capsys, monkeypatch, tmp_path_cwd):
        """Test that multiple report values from config are used."""
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[months]
months = ["janvier", "fevrier", "mars"]

[categories]
categories = ["out-foo", "out-bar"]

[report]
report = ["janvier,out-foo", "janvier,out-bar"]
"""
        config_path.write_text(config_content)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        # out-foo has value 0, out-bar has value 1334 in test spreadsheet
        self.assert_show(captured.out, 0)
        self.assert_show(captured.out, 1334)

    def test_cli_report_overrides_config_multiple(
        self, spreadsheet, capsys, monkeypatch, tmp_path_cwd
    ):
        """Test that explicit --report overrides config with multiple values."""
        config_path = tmp_path_cwd / ".easy-account.toml"
        config_content = """
[months]
months = ["janvier", "fevrier", "mars"]

[categories]
categories = ["out-foo", "out-bar"]

[report]
report = ["janvier,out-foo", "fevrier,out-bar"]
"""
        config_path.write_text(config_content)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "easy-account",
                "insert",
                str(spreadsheet),
                "mono user",
                "janvier",
                "out-bar",
                "100",
                "--report",
                "janvier,out-bar",
            ],
        )

        easy_account.cli.main()
        captured = capsys.readouterr()
        self.assert_show(captured.out, 1334)
        # Should only report one value, not the config's two values
        assert captured.out.count("Show content of") == 1
