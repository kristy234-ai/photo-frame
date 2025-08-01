"""
Google Photos integration for the Raspberry Pi photo frame.

This module handles Google OAuth credentials and downloads images from the
user's Google Photos library.  It stores OAuth tokens in `token.json` and
downloads images into the `photos/` directory.  Only the most recent
photographs are downloaded by default; you can customise the number of
photos downloaded and the query filters.

The Google Photos Library API returns a `baseUrl` property for each media
item.  To download an image while retaining metadata you must append the
`d` parameter (for “download”) to the base URL【746387997225079†L360-L376】.  The
`download_latest_photos` function implements this behaviour.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
]

DOWNLOAD_DIR = Path("photos")


def _load_credentials() -> Optional[Credentials]:
    """Load OAuth credentials from `token.json` if they exist and are valid.

    Returns:
        google.oauth2.credentials.Credentials if a valid token exists, else None.
    """
    if not os.path.exists("token.json"):
        return None
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds.valid:
        return None
    return creds


def get_service() -> Optional[object]:
    """Return an authorised Google Photos service instance or None if unauthorised."""
    creds = _load_credentials()
    if creds is None:
        return None
    try:
        service = build("photoslibrary", "v1", credentials=creds, static_discovery=False)
        return service
    except Exception as exc:
        print(f"Failed to build Google Photos service: {exc}")
        return None


def download_latest_photos(n: int = 5) -> List[str]:
    """Download the most recent `n` photos from the user's library.

    Images are saved into the `photos/` directory.  Existing files are not
    re‑downloaded.  If the user has fewer than `n` media items the function
    downloads as many as are available.

    Args:
        n: Number of latest photos to download.

    Returns:
        A list of file paths to the downloaded images.
    """
    service = get_service()
    if service is None:
        return []
    if not DOWNLOAD_DIR.exists():
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    paths: List[str] = []
    try:
        # Request the most recent media items
        response = service.mediaItems().list(pageSize=n).execute()
        items = response.get("mediaItems", [])
        for item in items:
            base_url = item.get("baseUrl")
            filename = item.get("filename")
            mime = item.get("mimeType", "")
            if not base_url or not filename or not mime.startswith("image/"):
                continue
            # Use the download parameter `=d` to download the full image with metadata
            url = f"{base_url}=d"
            file_path = DOWNLOAD_DIR / filename
            # Skip download if file already exists
            if file_path.exists():
                paths.append(str(file_path))
                continue
            r = requests.get(url)
            if r.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(r.content)
                paths.append(str(file_path))
    except HttpError as error:
        print(f"Google Photos API error: {error}")
    except Exception as exc:
        print(f"Error downloading photos: {exc}")
    return paths


def get_next_photo() -> Optional[str]:
    """Download at least one photo and return the path to the most recent file.

    If no photos are available the function returns None.
    """
    # Download at least one new photo
    download_latest_photos(1)
    # Collect image files with common extensions
    image_files = [
        f for f in DOWNLOAD_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    if not image_files:
        return None
    # Return the most recently modified image
    latest = max(image_files, key=lambda p: p.stat().st_mtime)
    return str(latest)