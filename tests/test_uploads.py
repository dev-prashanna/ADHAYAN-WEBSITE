"""Image upload validation and storage helpers."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from app.utils.uploads import UploadError, allowed_file, delete_image, save_image


def _png_upload(name="photo.png", size=(64, 64)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(10, 20, 30)).save(buffer, format="PNG")
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=name)


def test_allowed_file():
    assert allowed_file("a.png") is True
    assert allowed_file("a.WEBP") is True
    assert allowed_file("a.svg") is False
    assert allowed_file("") is False
    assert allowed_file(None) is False


def test_save_image_converts_to_webp(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = tmp_path
    with app.app_context():
        path = save_image(_png_upload())
    assert path.startswith("images/")
    assert path.endswith(".webp")
    assert (tmp_path / path).exists()


def test_save_image_rejects_bad_extension(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = tmp_path
    with app.app_context():
        with pytest.raises(UploadError):
            save_image(_png_upload(name="evil.svg"))


def test_save_image_rejects_non_image(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = tmp_path
    fake = FileStorage(stream=io.BytesIO(b"not an image at all"), filename="fake.png")
    with app.app_context():
        with pytest.raises(UploadError):
            save_image(fake)


def test_save_image_rejects_missing_file(app):
    with app.app_context():
        with pytest.raises(UploadError):
            save_image(None)


def test_save_image_downscales_large_images(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = tmp_path
    with app.app_context():
        path = save_image(_png_upload(size=(2600, 400)))
        stored = Image.open(tmp_path / path)
        assert max(stored.size) <= 1920


def test_delete_image_ignores_external_paths(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = tmp_path
    with app.app_context():
        delete_image("https://example.com/x.png")  # must not raise
        delete_image("")
        delete_image(None)
        # traversal attempt outside the upload root is ignored
        delete_image("../../etc/passwd")
