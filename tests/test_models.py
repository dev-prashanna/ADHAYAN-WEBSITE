"""Unit tests for models and small helpers."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Competition, Event, Project, SiteSetting, TeamMember, User
from app.utils.helpers import slugify, unique_slug


def test_slugify_basic():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Multiple   spaces  ") == "multiple-spaces"
    assert slugify("Ünïcödé Tîtle") == "unicode-title"
    assert slugify("") == "item"
    assert slugify("!!!") == "item"


def test_unique_slug_appends_counter(app):
    with app.app_context():
        first = unique_slug(Project, "My Project")
        db.session.add(Project(slug=first, title="My Project"))
        db.session.commit()
        second = unique_slug(Project, "My Project")
        assert second == "my-project-2"
        # excluding the own id keeps the slug stable on edit
        project = Project.query.filter_by(slug=first).one()
        assert unique_slug(Project, "My Project", exclude_id=project.id) == first


def test_password_hashing(app):
    with app.app_context():
        user = User(username="x")
        user.set_password("secret")
        assert user.password_hash != "secret"
        assert user.check_password("secret")
        assert not user.check_password("wrong")


def test_site_setting_get_set(app):
    with app.app_context():
        assert SiteSetting.get("missing", "fallback") == "fallback"
        SiteSetting.set("hero_title", "Test Hero", label="Hero", group="Homepage")
        db.session.commit()
        assert SiteSetting.get("hero_title") == "Test Hero"
        SiteSetting.set("hero_title", "Updated")
        db.session.commit()
        assert SiteSetting.get("hero_title") == "Updated"
        assert SiteSetting.query.filter_by(key="hero_title").count() == 1


def test_team_skill_list():
    member = TeamMember(name="A", skills="AI, ML , Robotics")
    assert member.skill_list == ["AI", "ML", "Robotics"]
    assert TeamMember(name="B").skill_list == []


def test_event_registration_open_logic(app):
    with app.app_context():
        future = datetime.utcnow() + timedelta(days=7)
        past = datetime.utcnow() - timedelta(days=1)

        open_event = Event(
            slug="open",
            title="Open",
            status="upcoming",
            registration_url="https://example.com",
            registration_deadline=future,
        )
        closed_no_url = Event(slug="nourl", title="No URL", status="upcoming")
        overdue = Event(
            slug="overdue",
            title="Overdue",
            status="upcoming",
            registration_url="https://example.com",
            registration_deadline=past,
        )
        completed = Competition(
            slug="done",
            title="Done",
            status="completed",
            registration_url="https://example.com",
        )
        assert open_event.registration_open is True
        assert closed_no_url.registration_open is False
        assert overdue.registration_open is False
        assert completed.registration_open is False
        assert open_event.is_upcoming is True


def test_project_tech_list():
    project = Project(title="P", tech_stack="Python, Flask, SQLite")
    assert project.tech_list == ["Python", "Flask", "SQLite"]
