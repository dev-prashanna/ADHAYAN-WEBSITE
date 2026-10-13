"""Application configuration.

Everything that differs between a laptop and a production Render instance is
driven by environment variables so no secret is ever committed to Git.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load ``.env`` when it exists (no dependency on python-dotenv being set up)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env")
    except Exception:  # pragma: no cover - dotenv is optional at runtime
        pass


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration."""

    # ------------------------------------------------------------------ core
    _load_dotenv()
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-insecure-secret-key"
    DEBUG = _as_bool(os.environ.get("FLASK_DEBUG"), False)
    TESTING = False

    # -------------------------------------------------------- persistent disk
    # SQLite and uploaded media must live on a persistent disk in production
    # (Render: mount a disk at /var/data and set DATA_DIR=/var/data).
    DATA_DIR = Path(os.environ.get("DATA_DIR") or (BASE_DIR / "instance")).resolve()
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + str(DATA_DIR / "adhayan.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER") or (DATA_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB request ceiling

    # ---------------------------------------------------------------- session
    PERMANENT_SESSION_LIFETIME = int(os.environ.get("SESSION_LIFETIME_SECONDS", 86400))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _as_bool(os.environ.get("SESSION_COOKIE_SECURE"), False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # ------------------------------------------------------------------- csrf
    WTF_CSRF_TIME_LIMIT = int(os.environ.get("WTF_CSRF_TIME_LIMIT", 3600))

    # ------------------------------------------------------------------ email
    # Optional SMTP delivery for the contact form. When unset the message is
    # only stored in the admin inbox, which keeps local development simple.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _as_bool(os.environ.get("MAIL_USE_TLS"), True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")
    CONTACT_RECIPIENT = os.environ.get("CONTACT_RECIPIENT", "")

    # ------------------------------------------------------------------ site
    SITE_URL = os.environ.get("SITE_URL", "http://localhost:5000")
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "hello@adhayan.org")

    # ------------------------------------------------------------- rate limit
    LOGIN_RATE_LIMIT = int(os.environ.get("LOGIN_RATE_LIMIT", 8))
    LOGIN_RATE_WINDOW = int(os.environ.get("LOGIN_RATE_WINDOW", 300))

    @classmethod
    def init_app(cls, app):
        """Create required folders on the persistent disk."""
        app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
        app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
