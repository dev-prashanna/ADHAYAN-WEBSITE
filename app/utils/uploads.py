"""Image upload helpers.

Uploads are written to the persistent disk (``UPLOAD_FOLDER``) and served by
the ``/media/<path>`` route. Files are validated, auto-rotated and downscaled
so the public pages stay fast on mobile connections.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf"}
MAX_IMAGE_SIDE = 1920
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024  # 16 MB ceiling for uploaded PDFs


class UploadError(ValueError):
    """Raised when a file cannot be accepted."""


def _extension(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def allowed_file(filename: str | None) -> bool:
    return bool(filename) and _extension(filename) in ALLOWED_EXTENSIONS


def save_document(file, subfolder: str = "documents") -> tuple[str, str, int]:
    """Store an uploaded PDF and return ``(relative_path, original_name, size)``.

    The file is kept as-is (no re-encoding) so the original PDF can be served
    and embedded. Only the extension is validated; the name is randomised.
    """
    if file is None or not file.filename:
        raise UploadError("No file selected.")

    if _extension(file.filename) not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise UploadError("Only PDF files can be uploaded.")

    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_DOCUMENT_BYTES:
        raise UploadError("PDF is larger than 16 MB.")
    if size == 0:
        raise UploadError("The uploaded file is empty.")

    raw = file.read()
    if not raw.startswith(b"%PDF"):
        raise UploadError("The file does not look like a valid PDF.")

    today = datetime.utcnow()
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / subfolder / f"{today:%Y}/{today:%m}"
    folder.mkdir(parents=True, exist_ok=True)

    name = f"{uuid.uuid4().hex}.pdf"
    (folder / name).write_bytes(raw)

    return f"{subfolder}/{today:%Y}/{today:%m}/{name}", Path(file.filename).name, size


def save_image(file, subfolder: str = "images") -> str:
    """Validate and store an uploaded image.

    Returns the storage path *relative to* ``UPLOAD_FOLDER``
    (e.g. ``images/2026/10/9f3a....webp``) which the media route can serve.
    """
    if file is None or not file.filename:
        raise UploadError("No file selected.")

    if not allowed_file(file.filename):
        raise UploadError(
            "Unsupported file type. Use PNG, JPG, WEBP or GIF."
        )

    # Stream to memory first so we never write an unvalidated file to disk.
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 8 * 1024 * 1024)
    if size > max_bytes:
        raise UploadError("File is larger than 8 MB.")

    try:
        image = Image.open(file.stream)
        image = ImageOps.exif_transpose(image)
    except Exception as exc:  # Pillow raises many exception types
        raise UploadError("The file is not a readable image.") from exc

    ext = _extension(file.filename)
    if ext == ".gif" and getattr(image, "is_animated", False):
        # Keep animated GIFs as-is.
        file.stream.seek(0)
        raw = file.read()
    else:
        image = _downscale(image)
        ext = ".webp"
        raw = _encode(image, ext)

    today = datetime.utcnow()
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / subfolder / f"{today:%Y}/{today:%m}"
    folder.mkdir(parents=True, exist_ok=True)

    name = f"{uuid.uuid4().hex}{ext}"
    (folder / name).write_bytes(raw)

    return f"{subfolder}/{today:%Y}/{today:%m}/{name}"


def _downscale(image: Image.Image) -> Image.Image:
    if max(image.size) > MAX_IMAGE_SIDE:
        image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.LANCZOS)
    return image


def _encode(image: Image.Image, ext: str) -> bytes:
    import io

    if image.mode in ("RGBA", "LA", "P"):
        # WebP keeps transparency; JPEG does not.
        if image.mode == "P":
            image = image.convert("RGBA")
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=84, method=4)
        return buffer.getvalue()

    if image.mode != "RGB":
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=84, method=4)
    return buffer.getvalue()


def delete_image(relative_path: str | None) -> None:
    """Best-effort removal of a previously stored upload."""
    if not relative_path or relative_path.startswith(("http://", "https://", "/")):
        return
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = (root / relative_path).resolve()
    if not str(target).startswith(str(root)):
        return
    try:
        target.unlink(missing_ok=True)
    except OSError:  # pragma: no cover
        pass
