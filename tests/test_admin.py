"""Authentication and admin CRUD workflows."""

from __future__ import annotations

from app.extensions import db
from app.models import Announcement, BlogPost, Competition, Project, SiteSetting, TeamMember


def test_login_required(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_login_success_and_logout(app, client):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-horse-battery"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")
    assert client.get("/admin/").status_code == 200

    response = client.post("/admin/logout", follow_redirects=False)
    assert response.status_code == 302
    assert client.get("/admin/", follow_redirects=False).status_code == 302


def test_login_wrong_password(app, client):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_project_create_edit_delete_roundtrip(app, admin_client):
    response = admin_client.post(
        "/admin/projects/new",
        data={
            "title": "Round Trip",
            "slug": "round-trip",
            "summary": "summary",
            "description": "body",
            "category": "Testing",
            "tech_stack": "Python",
            "contributors": "Tester",
            "github_url": "",
            "demo_url": "",
            "meta_description": "",
            "status": "published",
            "featured": "y",
            "sort_order": "1",
            "cover_image": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        project = Project.query.filter_by(slug="round-trip").one()
        assert project.featured is True
        assert project.status == "published"
        project_id = project.id

    # visible to the public
    assert admin_client.get("/projects/round-trip").status_code == 200

    # edit -> draft hides it publicly
    admin_client.post(
        f"/admin/projects/{project_id}/edit",
        data={
            "title": "Round Trip Edited",
            "slug": "round-trip",
            "summary": "updated",
            "description": "body",
            "category": "Testing",
            "tech_stack": "Python",
            "contributors": "Tester",
            "github_url": "",
            "demo_url": "",
            "meta_description": "",
            "status": "draft",
            "featured": "",
            "sort_order": "1",
            "cover_image": "",
        },
    )
    assert admin_client.get("/projects/round-trip").status_code == 404
    with app.app_context():
        assert Project.query.filter_by(slug="round-trip").one().title == "Round Trip Edited"

    # delete
    admin_client.post(f"/admin/projects/{project_id}/delete")
    with app.app_context():
        assert Project.query.filter_by(slug="round-trip").count() == 0


def test_blog_post_create_and_publish(app, admin_client):
    admin_client.post(
        "/admin/posts/new",
        data={
            "title": "Admin Post",
            "slug": "admin-post",
            "excerpt": "excerpt",
            "content": "# Hello",
            "author": "Admin",
            "category": "Research",
            "tags": "testing",
            "meta_description": "",
            "status": "published",
            "featured": "",
            "cover_image": "",
        },
    )
    assert admin_client.get("/blog/admin-post").status_code == 200
    with app.app_context():
        post = BlogPost.query.filter_by(slug="admin-post").one()
        post_id = post.id
    admin_client.post(f"/admin/posts/{post_id}/delete")
    with app.app_context():
        assert BlogPost.query.filter_by(slug="admin-post").count() == 0


def test_team_member_create_reorder_delete(app, admin_client):
    admin_client.post(
        "/admin/team/new",
        data={
            "name": "New Member",
            "slug": "new-member",
            "role": "Team member",
            "group": "team",
            "country": "Nowhere",
            "bio": "Bio",
            "skills": "Testing",
            "github_url": "",
            "linkedin_url": "",
            "website_url": "",
            "sort_order": "1",
            "is_active": "y",
            "featured": "",
            "portrait": "",
        },
    )
    with app.app_context():
        member = TeamMember.query.filter_by(slug="new-member").one()
        member_id = member.id
    assert b"New Member" in admin_client.get("/team").data

    # reorder endpoints respond (path parameter, not query string)
    assert (
        admin_client.post(f"/admin/team/{member_id}/move/up").status_code in (200, 302)
    )
    admin_client.post(f"/admin/team/{member_id}/delete")
    with app.app_context():
        assert TeamMember.query.filter_by(slug="new-member").count() == 0


def test_announcement_and_competition_crud(app, admin_client):
    admin_client.post(
        "/admin/announcements/new",
        data={
            "title": "Breaking",
            "slug": "breaking",
            "summary": "s",
            "body": "body",
            "category": "Update",
            "meta_description": "",
            "status": "published",
            "featured": "",
            "sort_order": "1",
            "image": "",
        },
    )
    assert admin_client.get("/news/breaking").status_code == 200

    admin_client.post(
        "/admin/competitions/new",
        data={
            "title": "Hackathon",
            "slug": "hackathon",
            "summary": "s",
            "description": "d",
            "category": "Competition",
            "starts_at": "2030-05-01T10:00",
            "ends_at": "",
            "location": "Online",
            "mode": "online",
            "registration_deadline": "",
            "registration_url": "https://example.com",
            "status": "upcoming",
            "meta_description": "",
            "sort_order": "1",
            "image": "",
        },
    )
    assert b"Hackathon" in admin_client.get("/events").data

    with app.app_context():
        ann_id = Announcement.query.filter_by(slug="breaking").one().id
        comp_id = Competition.query.filter_by(slug="hackathon").one().id
    admin_client.post(f"/admin/announcements/{ann_id}/delete")
    admin_client.post(f"/admin/competitions/{comp_id}/delete")
    with app.app_context():
        assert Announcement.query.filter_by(slug="breaking").count() == 0
        assert Competition.query.filter_by(slug="hackathon").count() == 0


def test_settings_edit_updates_public_copy(app, admin_client, seed):
    admin_client.post(
        "/admin/settings",
        data={"hero_title": "Custom Hero Headline"},
    )
    with app.app_context():
        assert SiteSetting.get("hero_title") == "Custom Hero Headline"
    assert b"Custom Hero Headline" in admin_client.get("/").data


def test_duplicate_slug_rejected(app, admin_client):
    admin_client.post(
        "/admin/projects/new",
        data={
            "title": "Original",
            "slug": "taken-slug",
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
        },
    )
    response = admin_client.post(
        "/admin/projects/new",
        data={
            "title": "Duplicate",
            "slug": "taken-slug",
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
        },
        follow_redirects=True,
    )
    assert b"already in use" in response.data
    with app.app_context():
        assert Project.query.filter_by(slug="taken-slug").count() == 1


def test_dashboard_shows_stats(admin_client, seed):
    response = admin_client.get("/admin/")
    assert response.status_code == 200
    assert b"Projects" in response.data


def test_login_rate_limiting(app, client):
    app.config["LOGIN_RATE_LIMIT"] = 3
    for _ in range(3):
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "wrong"},
            follow_redirects=True,
        )
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-horse-battery"},
        follow_redirects=True,
    )
    assert response.status_code == 429
