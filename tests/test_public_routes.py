"""Public visitor routes: pages render, filters work, drafts stay hidden."""

from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import Announcement, BlogPost, Competition, Event, Project, TeamMember


def _make_project(slug, title="T", category="AI", status="published", **kw):
    project = Project(slug=slug, title=title, category=category, status=status, **kw)
    db.session.add(project)
    db.session.commit()
    return project


def test_homepage_renders(client, seed):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ADHAYAN" in response.data


def test_pinned_projects_render_in_order_with_repository_links(client, seed):
    slugs = [
        "spatial-perception", "image-segmentation-naterida", "naterida",
        "cyphex", "guardrailer", "project-jerry",
    ]
    repositories = [
        "dev-prashanna/Spatial_Preception",
        "dev-prashanna/Image-Segmentation-Naterida",
        "DeV-PrasiddhA/NATERIDA", "dev-prashanna/CYPHEX",
        "dev-prashanna/Guardrailer", "dev-prashanna/PROJECT-JERRY",
    ]
    for path in ("/", "/projects"):
        page = client.get(path).get_data(as_text=True)
        positions = [page.index(f'href="/projects/{slug}"') for slug in slugs]
        assert positions == sorted(positions)
    for slug, repository in zip(slugs, repositories):
        detail = client.get(f"/projects/{slug}")
        assert detail.status_code == 200
        assert f'href="https://github.com/{repository}"' in detail.get_data(as_text=True)


def test_all_public_pages_render(client, seed):
    for path in [
        "/",
        "/about",
        "/projects",
        "/blog",
        "/team",
        "/news",
        "/events",
        "/contact",
        "/sitemap.xml",
        "/robots.txt",
    ]:
        response = client.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"


def test_seeded_content_visible(client, seed):
    assert b"Pitambar Lamichhane" in client.get("/team").data
    assert b"Introducing ADHAYAN" in client.get("/blog").data
    assert b"Weekly competition" in client.get("/news").data


def test_project_detail_and_404(client, app):
    with app.app_context():
        _make_project("demo-project", title="Demo Project")
    assert client.get("/projects/demo-project").status_code == 200
    assert client.get("/projects/does-not-exist").status_code == 404


def test_project_search_and_category_filter(client, app):
    with app.app_context():
        _make_project("alpha-vision", title="Alpha Vision", category="Computer Vision")
        _make_project("beta-nlp", title="Beta NLP", category="AI")
    response = client.get("/projects?q=Alpha")
    assert b"Alpha Vision" in response.data
    assert b"Beta NLP" not in response.data

    response = client.get("/projects?category=Computer%20Vision")
    assert b"Alpha Vision" in response.data
    assert b"Beta NLP" not in response.data


def test_draft_project_hidden_from_public(client, app):
    with app.app_context():
        _make_project("secret-draft", title="Secret Draft", status="draft")
    assert client.get("/projects/secret-draft").status_code == 404
    assert b"Secret Draft" not in client.get("/projects").data


def test_blog_detail_and_draft_hidden(client, app):
    with app.app_context():
        db.session.add(
            BlogPost(slug="pub-post", title="Public Post", status="published")
        )
        db.session.add(
            BlogPost(slug="draft-post", title="Draft Post", status="draft")
        )
        db.session.commit()
    assert client.get("/blog/pub-post").status_code == 200
    assert client.get("/blog/draft-post").status_code == 404


def test_news_detail(client, app):
    with app.app_context():
        db.session.add(
            Announcement(slug="a-news", title="A News", status="published")
        )
        db.session.commit()
    assert client.get("/news/a-news").status_code == 200


def test_events_page_splits_upcoming_and_completed(client, app):
    with app.app_context():
        db.session.add(
            Event(
                slug="soon",
                title="Upcoming Event",
                status="upcoming",
                starts_at=datetime(2030, 1, 1),
            )
        )
        db.session.add(
            Competition(
                slug="past",
                title="Past Competition",
                status="completed",
                starts_at=datetime(2020, 1, 1),
            )
        )
        db.session.commit()
    response = client.get("/events")
    assert b"Upcoming Event" in response.data
    assert b"Past Competition" in response.data


def test_contact_form_stores_message(client, app):
    response = client.post(
        "/contact",
        data={
            "name": "Visitor",
            "email": "visitor@example.com",
            "inquiry_type": "research",
            "subject": "Hello",
            "message": "This is a sufficiently long message.",
            "website": "",  # honeypot stays empty
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        from app.models import ContactMessage

        assert ContactMessage.query.count() == 1
        assert ContactMessage.query.one().email == "visitor@example.com"


def test_contact_honeypot_rejects_bots(client, app):
    response = client.post(
        "/contact",
        data={
            "name": "Bot",
            "email": "bot@example.com",
            "inquiry_type": "general",
            "message": "Automated spam message that is long enough.",
            "website": "http://spam.example",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        from app.models import ContactMessage

        assert ContactMessage.query.count() == 0


def test_sitemap_lists_published_content(client, app):
    with app.app_context():
        _make_project("site-seo-project", title="SEO Project")
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert b"site-seo-project" in response.data
    assert b"application/xml" in response.headers["Content-Type"].encode()


def test_robots_disallows_admin(client):
    response = client.get("/robots.txt")
    assert b"Disallow: /admin" in response.data


def test_media_route_serves_uploads(client, app, tmp_path):
    upload_dir = tmp_path / "uploads" / "images"
    upload_dir.mkdir(parents=True)
    (upload_dir / "pixel.png").write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d494844520000000100000001080600000"
            "01f15c4890000000d49444154789c626001000000ffff030000060005"
            "57bfabd40000000049454e44ae426082"
        )
    )
    app.config["UPLOAD_FOLDER"] = tmp_path / "uploads"
    response = client.get("/media/images/pixel.png")
    assert response.status_code == 200
