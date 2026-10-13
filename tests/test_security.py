"""Security behaviours: CSRF enforcement and admin authorisation."""

from __future__ import annotations

import re

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import Project, User


class CsrfTestConfig(TestConfig):
    WTF_CSRF_ENABLED = True


def _build_csrf_app():
    app = create_app(CsrfTestConfig)
    with app.app_context():
        _db.create_all()
        admin = User(username="admin")
        admin.set_password("pw")
        _db.session.add(admin)
        _db.session.commit()
    return app


def _token(html: bytes) -> str:
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', html)
    return match.group(1).decode() if match else ""


def _login(client, username="admin", password="pw"):
    """Sign in, supplying the CSRF token the login form requires."""
    token = _token(client.get("/admin/login").data)
    return client.post(
        "/admin/login",
        data={"username": username, "password": password, "csrf_token": token},
    )


def test_admin_mutations_rejected_without_csrf():
    app = _build_csrf_app()
    client = app.test_client()
    _login(client)
    # POST without any CSRF token must be refused
    response = client.post(
        "/admin/projects/new",
        data={"title": "NoToken", "slug": "no-token"},
    )
    assert response.status_code == 400
    with app.app_context():
        assert Project.query.count() == 0


def test_admin_mutation_succeeds_with_csrf_token():
    app = _build_csrf_app()
    client = app.test_client()
    _login(client)
    token = _token(client.get("/admin/projects/new").data)
    response = client.post(
        "/admin/projects/new",
        data={
            "title": "With Token",
            "slug": "with-token",
            "summary": "",
            "description": "",
            "category": "T",
            "tech_stack": "",
            "contributors": "",
            "github_url": "",
            "demo_url": "",
            "meta_description": "",
            "status": "published",
            "featured": "",
            "sort_order": "1",
            "cover_image": "",
            "csrf_token": token,
        },
    )
    assert response.status_code == 302
    with app.app_context():
        assert Project.query.filter_by(slug="with-token").count() == 1


def test_anonymous_cannot_reach_admin():
    app = _build_csrf_app()
    client = app.test_client()
    for path in [
        "/admin/",
        "/admin/projects",
        "/admin/posts/new",
        "/admin/settings",
    ]:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert "/admin/login" in response.headers["Location"]


def test_delete_form_embeds_hidden_csrf_input():
    """The delete buttons must post a named csrf_token field (regression test)."""
    app = _build_csrf_app()
    client = app.test_client()
    _login(client)
    with app.app_context():
        _db.session.add(Project(slug="p1", title="P1"))
        _db.session.commit()
    page = client.get("/admin/projects").data
    assert b'name="csrf_token"' in page
    assert b"/admin/projects/" in page and b"/delete" in page
