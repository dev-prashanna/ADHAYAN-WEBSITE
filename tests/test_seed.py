"""Content seed: fidelity to the source repository and idempotency."""

from __future__ import annotations

from app.extensions import db
from app.models import (
    Announcement,
    BlogPost,
    Competition,
    Event,
    Project,
    SiteSetting,
    TeamMember,
)


def test_seed_imports_expected_records(app):
    from app.seed import import_content

    with app.app_context():
        counts = import_content(db)
        assert counts["team"] == 14  # 10 cofounders + 4 national heads
        assert counts["projects"] >= 5
        assert counts["posts"] >= 2
        assert counts["announcements"] >= 1
        assert counts["competitions"] >= 1
        assert counts["settings"] > 50

        # real founder names from the AURA repository must be present
        names = {m.name for m in TeamMember.query.filter_by(group="cofounder").all()}
        for expected in [
            "Prashanna Tiwari",
            "Pitambar Lamichhane",
            "Ayan Zeeshan",
            "Shaidozzaman Araf",
            "Andrii Bilan",
            "Chanitha Sendinu Denagama",
            "Albert Rodrigo Alvarez Jove",
            "Aboubacar Bangoura",
            "Prince Kumar Mandal",
            "Peter R. Kandel",
        ]:
            assert expected in names, f"missing founder: {expected}"

        heads = {
            m.name for m in TeamMember.query.filter_by(group="national_head").all()
        }
        assert "Huzaifa Gulzar Shaikh" in heads
        assert "Serena Li" in heads


def test_seed_is_idempotent(app):
    from app.seed import import_content

    with app.app_context():
        first = import_content(db)
        totals_before = (
            TeamMember.query.count(),
            Project.query.count(),
            BlogPost.query.count(),
            Announcement.query.count(),
            Competition.query.count(),
        )
        second = import_content(db)
        totals_after = (
            TeamMember.query.count(),
            Project.query.count(),
            BlogPost.query.count(),
            Announcement.query.count(),
            Competition.query.count(),
        )
        assert totals_before == totals_after
        # second run inserts nothing new (settings may only backfill labels)
        assert second["team"] == 0
        assert second["projects"] == 0
        assert second["posts"] == 0
        assert second["announcements"] == 0
        assert first["team"] == 14


def test_seed_preserves_admin_edits(app):
    from app.seed import import_content

    with app.app_context():
        import_content(db)
        member = TeamMember.query.filter_by(slug="ayan-zeeshan").one()
        member.bio = "Edited by admin"
        db.session.commit()

        import_content(db)  # rerun must not overwrite
        assert TeamMember.query.filter_by(slug="ayan-zeeshan").one().bio == "Edited by admin"


def test_seed_upgrades_original_naterida_without_duplicate(app):
    from app.seed import PROJECT_RECORDS, import_content

    with app.app_context():
        db.session.add(Project(**PROJECT_RECORDS[0]))
        db.session.commit()
        original_id = Project.query.filter_by(slug="naterida").one().id
        import_content(db)
        project = Project.query.filter_by(slug="naterida").one()
        assert project.id == original_id
        assert project.github_url == "https://github.com/DeV-PrasiddhA/NATERIDA"
        assert project.sort_order == -40
        project.summary = "Edited project summary"
        project.status = "draft"
        db.session.commit()
        import_content(db)
        assert project.summary == "Edited project summary"
        assert project.status == "draft"


def test_seed_preserves_edited_legacy_naterida(app):
    from app.seed import PROJECT_RECORDS, import_content

    with app.app_context():
        record = dict(PROJECT_RECORDS[0], description="Custom project details")
        db.session.add(Project(**record))
        db.session.commit()
        import_content(db)
        project = Project.query.filter_by(slug="naterida").one()
        assert project.description == "Custom project details"
        assert project.github_url == ""


def test_seed_creates_all_site_setting_keys(app):
    from app.seed import DEFAULT_SETTINGS, import_content

    with app.app_context():
        import_content(db)
        keys = {row.key for row in SiteSetting.query.all()}
        for key, *_ in DEFAULT_SETTINGS:
            assert key in keys, f"missing setting: {key}"


def test_no_unused_event_rows_without_status(app):
    """Events seeded as competitions must land in the competitions table."""
    from app.seed import import_content

    with app.app_context():
        import_content(db)
        comp = Competition.query.first()
        assert comp is not None
        assert comp.status in {"upcoming", "completed", "cancelled"}
        for event in Event.query.all():
            assert event.status in {"upcoming", "completed", "cancelled"}
