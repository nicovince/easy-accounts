"""Tests for Infomaniak API module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from easy_account.infomaniak import (
    DownloadUrl,
    FileInfo,
    InfomaniakApi,
    InfomaniakApiError,
    MissingTokenError,
)


class TestInfomaniakApi:
    """Tests for InfomaniakApi class."""

    def test_missing_token_raises_error(self):
        """Test that MissingTokenError is raised when IK_TOKEN is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingTokenError) as exc_info:
                InfomaniakApi()
            assert "IK_TOKEN" in str(exc_info.value)

    def test_custom_token_is_used(self):
        """Test that custom token is used when provided."""
        api = InfomaniakApi(token="test_token")
        assert api.token == "test_token"

    def test_env_token_is_used_when_available(self, monkeypatch):
        """Test that IK_TOKEN env var is used when no token provided."""
        monkeypatch.setenv("IK_TOKEN", "env_token")
        api = InfomaniakApi()
        assert api.token == "env_token"

    def test_get_request_success(self, monkeypatch):
        """Test successful GET request."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        mock_response = {"result": "success", "data": {"id": 9, "name": "test.xlsx"}}

        with patch.object(api._session, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)

            result = api.get("https://api.test.com/endpoint")

            assert result == mock_response
            mock_get.assert_called_once()

    def test_get_request_failure(self, monkeypatch):
        """Test failed GET request raises InfomaniakApiError."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        with patch.object(api._session, "get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=500, json=lambda: {}, text="Internal Error"
            )

            with pytest.raises(InfomaniakApiError) as exc_info:
                api.get("https://api.test.com/endpoint")

            assert "500" in str(exc_info.value)

    def test_get_file_info(self, monkeypatch):
        """Test get_file_info returns FileInfo."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        mock_response = {
            "result": "success",
            "data": {
                "id": 9,
                "name": "macro-test.xlsx",
                "type": "file",
                "status": "ok",
                "drive_id": 1475057,
                "size": 16558,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        }

        with patch.object(api, "get", return_value=mock_response):
            file_info = api.get_file_info(1475057, 9)

            assert isinstance(file_info, FileInfo)
            assert file_info.id == 9
            assert file_info.name == "macro-test.xlsx"
            assert file_info.drive_id == 1475057
            assert file_info.size == 16558

    def test_get_temporary_download_url(self, monkeypatch):
        """Test get_temporary_download_url returns DownloadUrl."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        mock_response = {
            "result": "success",
            "data": {
                "temporary_url": "https://api.kdrive.infomaniak.com/drive/1475057/public/d/abc123.xlsx"
            },
        }

        with patch.object(api, "get", return_value=mock_response):
            download_url = api.get_temporary_download_url(1475057, 9)

            assert isinstance(download_url, DownloadUrl)
            assert (
                download_url.url
                == "https://api.kdrive.infomaniak.com/drive/1475057/public/d/abc123.xlsx"
            )

    def test_download_file_raises_when_file_exists(self, monkeypatch, tmp_path):
        """Test that download_file raises FileExistsError if file exists."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        existing_file = tmp_path / "test.xlsx"
        existing_file.write_text("existing content")

        with pytest.raises(FileExistsError) as exc_info:
            api.download_file(1475057, 9, str(existing_file))

        assert "already exists" in str(exc_info.value)

    def test_download_file_success(self, monkeypatch, tmp_path):
        """Test successful file download."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        mock_file_info = FileInfo(
            id=9, name="test.xlsx", drive_id=1475057, size=100, mime_type="application/vnd"
        )
        mock_download_url = DownloadUrl(url="https://download.test.com/file.xlsx")

        destination = tmp_path / "test.xlsx"

        with patch.object(api, "get_file_info", return_value=mock_file_info):
            with patch.object(api, "get_temporary_download_url", return_value=mock_download_url):
                with patch("requests.get") as mock_get:
                    mock_get.return_value = MagicMock(
                        status_code=200, iter_content=lambda chunk_size: [b"test content"]
                    )

                    api.download_file(1475057, 9, str(destination))

                    assert destination.exists()
                    assert destination.read_bytes() == b"test content"


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test FileInfo creation."""
        file_info = FileInfo(
            id=9, name="test.xlsx", drive_id=1475057, size=16558, mime_type="application/vnd"
        )
        assert file_info.id == 9
        assert file_info.name == "test.xlsx"
        assert file_info.drive_id == 1475057
        assert file_info.size == 16558
        assert file_info.mime_type == "application/vnd"


class TestDownloadUrl:
    """Tests for DownloadUrl dataclass."""

    def test_download_url_creation(self):
        """Test DownloadUrl creation."""
        download_url = DownloadUrl(url="https://test.com/download")
        assert download_url.url == "https://test.com/download"


class TestInfomaniakApiUpload:
    """Tests for InfomaniakApi upload_file method."""

    def test_upload_file_raises_when_file_not_found(self, monkeypatch):
        """Test that upload_file raises FileNotFoundError if local file doesn't exist."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        with pytest.raises(FileNotFoundError) as exc_info:
            api.upload_file(1475057, 9, "/nonexistent/file.xlsx")

        assert "not found" in str(exc_info.value)

    def test_upload_file_success(self, monkeypatch, tmp_path):
        """Test successful file upload."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"test content")

        with patch.object(api._session, "post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="success")

            api.upload_file(1475057, 9, str(test_file))

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            url = call_args.kwargs.get("url") or call_args[0][0]
            assert "total_size=12" in url
            assert "file_id=9" in url

    def test_upload_file_failure(self, monkeypatch, tmp_path):
        """Test failed file upload raises InfomaniakApiError."""
        monkeypatch.setenv("IK_TOKEN", "test_token")
        api = InfomaniakApi()

        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"test content")

        with patch.object(api._session, "post") as mock_post:
            mock_post.return_value = MagicMock(status_code=500, text="Internal Error")

            with pytest.raises(InfomaniakApiError) as exc_info:
                api.upload_file(1475057, 9, str(test_file))

            assert "500" in str(exc_info.value)
