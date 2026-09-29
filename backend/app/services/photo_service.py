"""Progress photo storage.

Files are written under a per-user directory with an opaque, generated name, so a
filename never leaks an identity and one user can never guess another's path. The
DB stores only the relative path; every read re-checks ownership before streaming
(spec 59).
"""
import secrets
from pathlib import Path

from fastapi import HTTPException, status

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 8 * 1024 * 1024  # 8 MB


def user_dir(media_root: Path, user_id: int) -> Path:
    d = media_root / "progress_photos" / str(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_photo(media_root: Path, user_id: int, content: bytes, content_type: str) -> tuple[str, int]:
    """Validate and store a photo. Returns (relative_stored_name, size_bytes)."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Photos must be JPEG, PNG or WebP.",
        )
    if not content:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "The uploaded file is empty.")
    if len(content) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Photos must be 8 MB or smaller.")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]
    name = f"{secrets.token_hex(16)}.{ext}"
    path = user_dir(media_root, user_id) / name
    path.write_bytes(content)
    return f"progress_photos/{user_id}/{name}", len(content)


def delete_photo(media_root: Path, stored_name: str) -> None:
    """Remove the file if it exists; a missing file is not an error."""
    path = media_root / stored_name
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def photo_path(media_root: Path, stored_name: str) -> Path:
    path = media_root / stored_name
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo file is missing.")
    return path
