"""Shared pytest fixtures.

The application is built with an in-memory SQLite database and CSRF disabled
for ordinary form posts; ``test_security.py`` re-enables CSRF to prove the
protection is actually enforced.
"""

from __future__ import annotations

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import User


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    # Setup runs inside its own app context, which is popped before the test
    # body so that each client request pushes a fresh app context (and a fresh
    # ``flask.g``), exactly like the per-request contexts in production.
    with app.app_context():
        _db.create_all()
        admin = User(username="admin", email="admin@example.com")
        admin.set_password("correct-horse-battery")
        _db.session.add(admin)
        _db.session.commit()
    yield app
    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_client(app, client):
    """A client already signed in as the administrator."""
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-horse-battery"},
        follow_redirects=True,
    )
    return client


@pytest.fixture()
def seed(app):
    """Run the idempotent content seed inside a request-free context."""
    from app.seed import import_content

    with app.app_context():
        counts = import_content(_db)
        return counts
