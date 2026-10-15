"""Public research pages and the member join / upload flow."""

from __future__ import annotations

from io import BytesIO

from app.extensions import db
from app.models import Member, Publication


def _make_publication(slug, title="Paper", status="published", **kw):
    pub = Publication(slug=slug, title=title, author_name="Ada", status=status, **kw)
    db.session.add(pub)
    db.session.commit()
    return pub


def _make_member(email="ada@example.com", status="pending", name="Ada Lovelace"):
    member = Member(email=email, name=name, application_status=status)
    db.session.add(member)
    db.session.commit()
    return member.id


def _sign_in(client, member_id):
    with client.session_transaction() as sess:
        sess["member_id"] = member_id


def _tiny_pdf():
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF\n"


# ---------------------------------------------------------------- public pages
def test_research_index_and_detail_render(client, seed):
    index = client.get("/research")
    assert index.status_code == 200
    # The seeded Zenodo-style paper shows on the public list.
    assert b"Lightweight Prompt Injection Detection" in index.data

    detail = client.get("/research/lightweight-prompt-injection-detection")
    assert detail.status_code == 200
    page = detail.get_data(as_text=True)
    assert "Abstract" in page
    assert "Files" in page
    assert "Software" in page
    assert "References" in page
    assert "10.5281/zenodo.22124698" in page


def test_research_detail_404_and_draft_hidden(client, app):
    with app.app_context():
        _make_publication("open-paper", title="Open Paper")
        _make_publication("hidden-paper", title="Hidden Paper", status="draft")
    assert client.get("/research/open-paper").status_code == 200
    assert client.get("/research/hidden-paper").status_code == 404
    assert b"Hidden Paper" not in client.get("/research").data


def test_repository_papers_have_working_pdfs_and_preserve_edits(client, app):
    from app.repository_publications import import_repository_publications

    slugs = (
        "autonomous-edge-robotics-bc-vs-dqn",
        "semantic-segmentation-autonomous-agricultural-robots",
    )
    with app.app_context():
        assert import_repository_publications(db) == 2
        db.session.commit()
        papers = Publication.query.filter(Publication.slug.in_(slugs)).all()
        for paper in papers:
            assert paper.pdf_size > 100_000
            assert paper.author_name == "Prashanna Tiwari"
            assert paper.abstract and paper.reference_list
            response = client.get(f"/media/{paper.pdf_path}")
            assert response.status_code == 200
            assert response.mimetype == "application/pdf"
            assert response.data.startswith(b"%PDF-")
        papers[0].title = "Edited by the author"
        db.session.commit()
        assert import_repository_publications(db) == 0
        assert Publication.query.get(papers[0].id).title == "Edited by the author"

    for slug in slugs:
        assert client.get(f"/research/{slug}").status_code == 200
    assert b"July 2026" in client.get(f"/research/{slugs[1]}").data


def test_research_search(client, app):
    with app.app_context():
        _make_publication("alpha-paper", title="Alpha Vision Paper")
        _make_publication("beta-paper", title="Beta NLP Paper")
    response = client.get("/research?q=Alpha")
    assert b"Alpha Vision Paper" in response.data
    assert b"Beta NLP Paper" not in response.data


# ------------------------------------------------------------- join gating
def test_join_requires_google_signin(client):
    response = client.get("/join", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "/auth/google" in location or "accounts.google.com" in location


def test_account_and_upload_require_approved_member(client, app):
    with app.app_context():
        pending_id = _make_member("pending@example.com", status="pending")
    _sign_in(client, pending_id)
    # Pending member is pushed to the join form, not the upload page.
    response = client.get("/account/research/new", follow_redirects=True)
    assert response.status_code == 200
    assert "/join" in response.get_data(as_text=True)


def test_join_flow_approves_curious_applicant(client, app, monkeypatch):
    from app.routes import members as members_module

    monkeypatch.setattr(
        members_module, "score_application", lambda essay: (9, "Genuine curiosity.")
    )
    with app.app_context():
        member_id = _make_member("grace@example.com", status="pending", name="")
    _sign_in(client, member_id)

    response = client.post(
        "/join",
        data={
            "name": "Grace Hopper",
            "email": "grace@example.com",
            "application_essay": (
                "I am fascinated by compiler design and want to understand how "
                "optimisation passes transform intermediate representations. "
                "I would love to collaborate because reviewing others' code "
                "teaches me faster than working alone, and I hope to co-author "
                "a paper on lightweight optimisation heuristics with peers "
                "who know formal methods better than I do right now."
            ),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        member = Member.query.filter_by(email="grace@example.com").one()
        assert member.is_approved
        assert member.name == "Grace Hopper"
        assert member.essay_score == 9
        assert "compiler design" in member.application_essay


def test_join_flow_rejects_low_score(client, app, monkeypatch):
    from app.routes import members as members_module

    monkeypatch.setattr(
        members_module, "score_application", lambda essay: (3, "Generic and self-serving.")
    )
    with app.app_context():
        member_id = _make_member("spam@example.com", status="pending", name="")
    _sign_in(client, member_id)

    response = client.post(
        "/join",
        data={
            "name": "Spam Applicant",
            "email": "spam@example.com",
            "application_essay": (
                "I want to join because it looks good on my CV and I need "
                "publications for my resume. Please accept me as soon as "
                "possible, I do not really care about the research itself."
            ),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        member = Member.query.filter_by(email="spam@example.com").one()
        assert member.application_status == "rejected"
        assert not member.is_approved
        assert member.essay_score == 3


def test_join_flow_pending_when_scoring_unavailable(client, app, monkeypatch):
    from app.routes import members as members_module

    monkeypatch.setattr(
        members_module, "score_application", lambda essay: (None, "No API key.")
    )
    with app.app_context():
        member_id = _make_member("hold@example.com", status="pending", name="")
    _sign_in(client, member_id)

    response = client.post(
        "/join",
        data={
            "name": "Hold Applicant",
            "email": "hold@example.com",
            "application_essay": (
                "I am curious about distributed systems and want to learn by "
                "collaborating with others on open-source infrastructure projects."
            ),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        member = Member.query.filter_by(email="hold@example.com").one()
        assert member.application_status == "pending"
        assert member.essay_score is None


# ------------------------------------------------------------------ upload
def test_approved_member_can_upload_research(client, app):
    with app.app_context():
        member_id = _make_member("alan@example.com", status="approved", name="Alan Turing")
    _sign_in(client, member_id)

    response = client.post(
        "/account/research/new",
        data={
            "title": "On Computable Numbers",
            "abstract": "A formal presentation of the Turing machine and the halting problem.",
            "keywords": "computability, Turing machine",
            "license": "CC BY 4.0",
            "github_url": "https://github.com/example/machine",
            "dataset_url": "https://example.com/data",
            "software_language": "Python",
            "software_status": "Active",
            "references": "Turing, A. (1936)",
            "pdf_upload": (BytesIO(_tiny_pdf()), "paper.pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        pub = Publication.query.filter_by(slug="on-computable-numbers").one()
        assert pub.author_name == "Alan Turing"
        assert pub.status == "published"
        assert pub.has_pdf
        assert pub.pdf_filename == "paper.pdf"
        slug = pub.slug
    # The detail page now renders the uploaded record.
    detail = client.get(f"/research/{slug}")
    assert detail.status_code == 200
    assert b"On Computable Numbers" in detail.data


def test_upload_without_pdf_is_rejected(client, app):
    with app.app_context():
        member_id = _make_member("linus@example.com", status="approved", name="Linus")
    _sign_in(client, member_id)

    response = client.post(
        "/account/research/new",
        data={
            "title": "No File Paper",
            "abstract": "An abstract long enough to satisfy the minimum length validator.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Publication.query.filter_by(slug="no-file-paper").first() is None


def test_member_logout(client, app):
    with app.app_context():
        member_id = _make_member("out@example.com", status="approved")
    _sign_in(client, member_id)
    client.post("/account/logout", follow_redirects=True)
    # After signing out, gated pages bounce to Google sign-in again.
    response = client.get("/account", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "/auth/google" in location or "accounts.google.com" in location
