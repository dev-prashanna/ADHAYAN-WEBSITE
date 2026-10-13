"""Small shared helpers: slugs, settings, rate limiting and e-mail delivery."""

from __future__ import annotations

import re
import smtplib
import time
import unicodedata
from email.message import EmailMessage
from threading import Lock

from flask import current_app, g

from app.models import SiteSetting

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(value: str, fallback: str = "item") -> str:
    """URL-safe slug (ASCII only, stable across languages)."""
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = _SLUG_STRIP.sub("-", value).strip("-")
    return value or fallback


def unique_slug(model, value: str, exclude_id: int | None = None) -> str:
    """Append ``-2``, ``-3`` ... until the slug is free for ``model``."""
    base = slugify(value)
    candidate = base
    counter = 2
    while True:
        query = model.query.filter_by(slug=candidate)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if query.first() is None:
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1


def settings() -> dict[str, str]:
    """All site settings for the current request (cached on ``flask.g``)."""
    if not hasattr(g, "_site_settings"):
        g._site_settings = {row.key: row.value for row in SiteSetting.query.all()}
    return g._site_settings


def setting(key: str, default: str = "") -> str:
    return settings().get(key, default)


# --------------------------------------------------------------------- rate limit
_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_LOGIN_LOCK = Lock()


def rate_limit_exceeded(identifier: str) -> bool:
    """True when ``identifier`` (usually the client IP) exceeded the login limit."""
    limit = current_app.config["LOGIN_RATE_LIMIT"]
    window = current_app.config["LOGIN_RATE_WINDOW"]
    now = time.monotonic()
    with _LOGIN_LOCK:
        hits = [t for t in _LOGIN_ATTEMPTS.get(identifier, []) if now - t < window]
        _LOGIN_ATTEMPTS[identifier] = hits
        return len(hits) >= limit


def record_attempt(identifier: str) -> None:
    now = time.monotonic()
    with _LOGIN_LOCK:
        _LOGIN_ATTEMPTS.setdefault(identifier, []).append(now)


def reset_attempts(identifier: str) -> None:
    with _LOGIN_LOCK:
        _LOGIN_ATTEMPTS.pop(identifier, None)


# ------------------------------------------------------------------------- email
def send_email(subject: str, body: str, sender: str, recipients: list[str]) -> bool:
    """Send a plain-text e-mail over SMTP.

    Returns ``False`` (instead of raising) when e-mail is not configured, so the
    contact form keeps working in local development.
    """
    server = current_app.config.get("MAIL_SERVER", "")
    if not server:
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config.get("MAIL_DEFAULT_SENDER") or sender
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        port = current_app.config.get("MAIL_PORT", 587)
        with smtplib.SMTP(server, port, timeout=15) as smtp:
            if current_app.config.get("MAIL_USE_TLS"):
                smtp.starttls()
            username = current_app.config.get("MAIL_USERNAME", "")
            if username:
                smtp.login(username, current_app.config.get("MAIL_PASSWORD", ""))
            smtp.send_message(message)
        return True
    except Exception as exc:  # pragma: no cover - depends on live SMTP
        current_app.logger.warning("Contact e-mail not delivered: %s", exc)
        return False
