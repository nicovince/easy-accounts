"""Infomaniak API client for kdrive operations."""

import os
import sys
from dataclasses import dataclass
from typing import Any
from pathlib import Path

import requests


class InfomaniakApiError(Exception):
    """Raised when Infomaniak API call fails."""

    pass


class MissingTokenError(Exception):
    """Raised when IK_TOKEN environment variable is not set."""

    pass


class InfomaniakInvalidApiUrl(Exception):
    """Raised when the API url could not be parsed."""

    pass


class InfomaniakFileAlreadyExists(Exception):
    """Raised when file already exists."""

    pass


@dataclass
class FileInfo:
    """Information about a file from Infomaniak kdrive."""

    id: int
    name: str
    drive_id: int
    size: int
    mime_type: str


@dataclass
class DownloadUrl:
    """Temporary download URL for a file."""

    url: str


class InfomaniakApi:
    """Client for Infomaniak kdrive API."""

    BASE_URL = "https://api.infomaniak.com/2/drive"

    def __init__(self, token: str | None = None):
        """Initialize the API client.

        Args:
            token: API token. If None, reads from IK_TOKEN env var.
        """
        if token is None:
            token = os.environ.get("IK_TOKEN")
            if token is None:
                raise MissingTokenError(
                    "IK_TOKEN environment variable not set. "
                    "Please create a token with the drive scope at "
                    "https://manager.infomaniak.com/v3/1285210/ng/profile/user/token/list"
                )
        self._token = token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )

    @property
    def token(self) -> str:
        """Get the API token."""
        return self._token

    def get(self, url: str, params: dict | None = None) -> dict[str, Any]:
        """Perform a GET request to the Infomaniak API.

        Args:
            url: The API endpoint URL.
            params: Optional query parameters.

        Returns:
            JSON response as a dictionary.

        Raises:
            InfomaniakApiError: If the API request fails.
        """
        response = self._session.get(url, params=params)
        if response.status_code != 200:
            raise InfomaniakApiError(
                f"API request failed with status {response.status_code}: {response.text}"
            )
        return response.json()

    def url_to_file_info(self, api_url: str) -> FileInfo:
        """Convert API url to FileInfo

        Args:
            api_url: The Infomaniak API of the file

        Returns:
            FileInfo object with file metadata.
        """
        parsed = api_url.rstrip("/").split("/")
        try:
            drive_id = int(parsed[-3])
            file_id = int(parsed[-1])
        except (IndexError, ValueError):
            raise InfomaniakInvalidApiUrl(f"Invalid Infomaniak API URL: {api_url}")

        return self.get_file_info(drive_id, file_id)

    def get_file_info(self, drive_id: int, file_id: int) -> FileInfo:
        """Get information about a file.

        Args:
            drive_id: The drive ID.
            file_id: The file ID.

        Returns:
            FileInfo object with file metadata.

        Raises:
            InfomaniakApiError: If the API request fails.
        """
        url = f"{self.BASE_URL}/{drive_id}/files/{file_id}"
        data = self.get(url)
        if data.get("result") != "success":
            raise InfomaniakApiError(f"API returned error: {data}")
        file_data = data.get("data", {})
        return FileInfo(
            id=file_data["id"],
            name=file_data["name"],
            drive_id=file_data["drive_id"],
            size=file_data["size"],
            mime_type=file_data["mime_type"],
        )

    def get_temporary_download_url(self, drive_id: int, file_id: int) -> DownloadUrl:
        """Get a temporary download URL for a file.

        Args:
            drive_id: The drive ID.
            file_id: The file ID.

        Returns:
            DownloadUrl object with the temporary URL.

        Raises:
            InfomaniakApiError: If the API request fails.
        """
        url = f"{self.BASE_URL}/{drive_id}/files/{file_id}/temporary_url"
        data = self.get(url)
        if data.get("result") != "success":
            raise InfomaniakApiError(f"API returned error: {data}")
        return DownloadUrl(url=data["data"]["temporary_url"])

    BASE_URL_V3 = "https://api.infomaniak.com/3/drive"

    def download_file(self, drive_id: int, file_id: int, destination: str) -> None:
        """Download a file from kdrive.

        Args:
            drive_id: The drive ID.
            file_id: The file ID.
            destination: Path where to save the file.

        Raises:
            InfomaniakApiError: If the API request fails.
        """
        if os.path.exists(destination):
            raise FileExistsError(f"File already exists: {destination}")

        download_url = self.get_temporary_download_url(drive_id, file_id)

        response = requests.get(download_url.url, stream=True)
        if response.status_code != 200:
            raise InfomaniakApiError(
                f"Download failed with status {response.status_code}: {response.text}"
            )

        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def upload_file(self, drive_id: int, file_id: int, file_path: str) -> None:
        """Upload/update a file to kdrive.

        Args:
            drive_id: The drive ID.
            file_id: The file ID to update.
            file_path: Path to the local file to upload.

        Raises:
            InfomaniakApiError: If the API request fails.
            FileNotFoundError: If the local file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        url = f"{self.BASE_URL_V3}/{drive_id}/upload?total_size={file_size}&file_id={file_id}"

        headers = {
            "Authorization": f"Bearer {self.token}",
        }

        with open(file_path, "rb") as f:
            response = self._session.post(url, headers=headers, data=f)

        if response.status_code not in (200, 201):
            raise InfomaniakApiError(
                f"Upload failed with status {response.status_code}: {response.text}"
            )


def pull_file(url: str, api: InfomaniakApi | None = None) -> str:
    parsed = url.rstrip("/").split("/")
    try:
        drive_id = int(parsed[-3])
        file_id = int(parsed[-1])
    except (IndexError, ValueError):
        print(
            "Error: Invalid API URL format. Expected "
            "https://api.infomaniak.com/2/drive/<drive_id>/files/<file_id>",
            file=sys.stderr,
        )
        raise InfomaniakInvalidApiUrl(f"Invalid Infomaniak API URL: {url}")

    if api is None:
        api = InfomaniakApi()
    file_info = api.get_file_info(drive_id, file_id)
    destination = Path(file_info.name)

    if destination.exists():
        raise InfomaniakFileAlreadyExists(f"File {destination} already exists")

    api.download_file(drive_id, file_id, str(destination))
    return str(destination)
