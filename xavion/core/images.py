"""Validate, persist, and serialize local images for multimodal conversations."""

from __future__ import annotations

import base64
import binascii
import re
import uuid
from pathlib import Path
from typing import Any

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGES_PER_MESSAGE = 4

# The MIME type comes from the image header, not an untrusted filename or claim.
_IMAGE_FORMATS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
_IMAGE_ID = re.compile(r"^[0-9a-f]{32}$")
_DATA_URI = re.compile(r"^data:(image/[\w.+-]+);base64,(.+)$", re.DOTALL)


def _detect_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Unsupported image format. Use PNG, JPEG, or WebP.")


def _read_source(source: Any) -> tuple[bytes, str | None]:
    if isinstance(source, bytes):
        return source, None

    if not isinstance(source, dict):
        raise ValueError("An image must contain 'path', 'data', or 'base64'.")

    keys = [key for key in ("path", "data", "base64") if key in source]
    if len(keys) != 1:
        raise ValueError("Specify exactly one image source: path, data, or base64.")

    claimed_mime = source.get("mime_type")
    if claimed_mime is not None and not isinstance(claimed_mime, str):
        raise ValueError("Image mime_type must be a string.")

    if keys[0] == "path":
        path = source["path"]
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Image path must be a non-empty string.")
        file_path = Path(path).expanduser()
        if not file_path.is_file():
            raise ValueError(f"Image file does not exist: {file_path}")
        if file_path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image exceeds the 8 MiB limit.")
        return file_path.read_bytes(), claimed_mime

    encoded = source[keys[0]]
    if not isinstance(encoded, str) or not encoded.strip():
        raise ValueError("Image base64 data must be a non-empty string.")

    match = _DATA_URI.fullmatch(encoded.strip())
    if match:
        uri_mime, encoded = match.groups()
        if claimed_mime is not None and claimed_mime != uri_mime:
            raise ValueError("Image MIME types do not match.")
        claimed_mime = uri_mime

    encoded = encoded.strip()
    if len(encoded) > ((MAX_IMAGE_BYTES + 2) // 3) * 4 + 4:
        raise ValueError("Image exceeds the 8 MiB limit.")

    try:
        return base64.b64decode(encoded, validate=True), claimed_mime
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 image data.") from exc


class ImageStore:
    """Keep binary attachments outside conversation JSON files."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.image_dir = Path(data_dir) / "images"

    def save_many(self, sources: list[Any]) -> list[dict[str, Any]]:
        if len(sources) > MAX_IMAGES_PER_MESSAGE:
            raise ValueError(f"A message can contain at most {MAX_IMAGES_PER_MESSAGE} images.")

        attachments: list[dict[str, Any]] = []
        try:
            for source in sources:
                data, claimed_mime = _read_source(source)
                if not data:
                    raise ValueError("Image cannot be empty.")
                if len(data) > MAX_IMAGE_BYTES:
                    raise ValueError("Image exceeds the 8 MiB limit.")

                actual_mime = _detect_mime(data)
                if claimed_mime and claimed_mime != actual_mime:
                    raise ValueError("Image MIME type does not match its file content.")

                image_id = uuid.uuid4().hex
                self.image_dir.mkdir(parents=True, exist_ok=True)
                destination = self.image_dir / f"{image_id}{_IMAGE_FORMATS[actual_mime]}"
                with destination.open("xb") as image_file:
                    image_file.write(data)

                attachments.append(
                    {"id": image_id, "mime_type": actual_mime, "size": len(data)}
                )
        except Exception:
            self.remove_many(attachments)
            raise

        return attachments

    def remove_many(self, attachments: list[dict[str, Any]]) -> None:
        for attachment in attachments:
            try:
                path = self._path_for(attachment)
                path.unlink(missing_ok=True)
            except (ValueError, OSError):
                pass

    def _path_for(self, attachment: dict[str, Any]) -> Path:
        image_id = attachment.get("id")
        mime_type = attachment.get("mime_type")
        if not isinstance(image_id, str) or not _IMAGE_ID.fullmatch(image_id):
            raise ValueError("Invalid stored image ID.")
        if mime_type not in _IMAGE_FORMATS:
            raise ValueError("Invalid stored image MIME type.")
        return self.image_dir / f"{image_id}{_IMAGE_FORMATS[mime_type]}"

    def content_for_message(
        self,
        text: str,
        attachments: list[dict[str, Any]],
    ) -> str | list[dict[str, Any]]:
        if not attachments:
            return text

        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        for attachment in attachments:
            path = self._path_for(attachment)
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise ValueError(f"Stored image is unavailable: {attachment['id']}") from exc
            if len(data) > MAX_IMAGE_BYTES or _detect_mime(data) != attachment["mime_type"]:
                raise ValueError(f"Stored image is invalid: {attachment['id']}")
            encoded = base64.b64encode(data).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{attachment['mime_type']};base64,{encoded}"},
                }
            )
        return content
