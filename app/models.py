"""Database models.

The schema is intentionally small: every piece of public content lives in the
database so that nothing is hard-coded into Jinja templates.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

PUBLISH_STATES = ("draft", "published")
EVENT_STATUSES = ("upcoming", "completed", "cancelled")
EVENT_MODES = ("online", "in_person", "hybrid")
PEER_GROUPS = ("cofounder", "national_head", "team")


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite stores naive datetimes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class PublishableMixin:
    status = db.Column(db.String(16), default="published", nullable=False, index=True)
    featured = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def is_published(self) -> bool:
        return self.status == "published"


class User(UserMixin, db.Model):
    """A single administrator account (more can be added later)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username}>"


APPLICATION_STATUSES = ("pending", "approved", "rejected")


class Member(TimestampMixin, db.Model):
    """A researcher who joined via Google and can submit papers.

    Members are separate from administrator ``User`` accounts: they sign in
    with Google OAuth and only gain access after submitting an application.
    """

    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(160), default="", nullable=False)
    avatar_url = db.Column(db.String(400), default="", nullable=False)
    research_interests = db.Column(db.Text, default="", nullable=False)
    application_essay = db.Column(db.Text, default="", nullable=False)
    essay_score = db.Column(db.Integer, nullable=True)
    application_status = db.Column(
        db.String(16), default="pending", nullable=False, index=True
    )
    applied_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_approved(self) -> bool:
        return self.application_status == "approved"

    @property
    def initials(self) -> str:
        parts = (self.name or self.email or "?").split()
        return "".join(p[0].upper() for p in parts[:2]) if parts else "?"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Member {self.email}>"


class Project(TimestampMixin, PublishableMixin, db.Model):
    __tablename__ = "projects"

    @property
    def cover_credit(self):
        from app.project_covers import PROJECT_COVERS, cover_path

        if self.cover_image == cover_path(self.slug):
            return PROJECT_COVERS.get(self.slug)
        return None

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(400), default="", nullable=False)
    description = db.Column(db.Text, default="", nullable=False)  # Markdown
    category = db.Column(db.String(80), default="Other", nullable=False, index=True)
    tech_stack = db.Column(db.String(400), default="", nullable=False)  # comma list
    contributors = db.Column(db.String(400), default="", nullable=False)  # comma list
    cover_image = db.Column(db.String(300), default="", nullable=False)
    github_url = db.Column(db.String(400), default="", nullable=False)
    demo_url = db.Column(db.String(400), default="", nullable=False)
    meta_description = db.Column(db.String(300), default="", nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False, index=True)

    @property
    def tech_list(self) -> list[str]:
        return [t.strip() for t in (self.tech_stack or "").split(",") if t.strip()]

    @property
    def contributor_list(self) -> list[str]:
        return [c.strip() for c in (self.contributors or "").split(",") if c.strip()]


class BlogPost(TimestampMixin, PublishableMixin, db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(220), nullable=False)
    excerpt = db.Column(db.String(400), default="", nullable=False)
    content = db.Column(db.Text, default="", nullable=False)  # Markdown
    author = db.Column(db.String(160), default="", nullable=False)
    category = db.Column(db.String(80), default="Research", nullable=False, index=True)
    tags = db.Column(db.String(300), default="", nullable=False)  # comma list
    cover_image = db.Column(db.String(300), default="", nullable=False)
    meta_description = db.Column(db.String(300), default="", nullable=False)
    published_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    @property
    def tag_list(self) -> list[str]:
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]


class TeamMember(TimestampMixin, db.Model):
    __tablename__ = "team_members"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    role = db.Column(db.String(160), default="Co-Founder", nullable=False)
    group = db.Column(db.String(40), default="cofounder", nullable=False, index=True)
    country = db.Column(db.String(80), default="", nullable=False)
    bio = db.Column(db.Text, default="", nullable=False)
    skills = db.Column(db.String(400), default="", nullable=False)  # comma list
    portrait = db.Column(db.String(300), default="", nullable=False)
    github_url = db.Column(db.String(400), default="", nullable=False)
    linkedin_url = db.Column(db.String(400), default="", nullable=False)
    website_url = db.Column(db.String(400), default="", nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def skill_list(self) -> list[str]:
        return [s.strip() for s in (self.skills or "").split(",") if s.strip()]


class Announcement(TimestampMixin, PublishableMixin, db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(220), nullable=False)
    summary = db.Column(db.String(400), default="", nullable=False)
    body = db.Column(db.Text, default="", nullable=False)  # Markdown
    category = db.Column(db.String(80), default="Announcement", nullable=False)
    image = db.Column(db.String(300), default="", nullable=False)
    meta_description = db.Column(db.String(300), default="", nullable=False)
    published_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)


class EventBase:
    """Columns shared by events and competitions.

    Both collections are stored in their own table (as listed in the project
    spec) but reuse exactly the same fields, so the admin forms and templates
    are shared too.
    """

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text, default="", nullable=False)  # Markdown
    summary = db.Column(db.String(400), default="", nullable=False)
    image = db.Column(db.String(300), default="", nullable=False)
    starts_at = db.Column(db.DateTime, nullable=True, index=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), default="", nullable=False)
    mode = db.Column(db.String(20), default="online", nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    registration_url = db.Column(db.String(400), default="", nullable=False)
    status = db.Column(db.String(20), default="upcoming", nullable=False, index=True)
    category = db.Column(db.String(80), default="", nullable=False)
    meta_description = db.Column(db.String(300), default="", nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    @property
    def is_upcoming(self) -> bool:
        return self.status == "upcoming"

    @property
    def registration_open(self) -> bool:
        if self.status != "upcoming":
            return False
        if self.registration_deadline and self.registration_deadline < utcnow():
            return False
        return bool(self.registration_url)


class Event(EventBase, db.Model):
    __tablename__ = "events"
    kind = db.Column(db.String(20), default="event", nullable=False)

    @property
    def type_label(self) -> str:
        return "Event"


class Competition(EventBase, db.Model):
    __tablename__ = "competitions"
    kind = db.Column(db.String(20), default="competition", nullable=False)

    @property
    def type_label(self) -> str:
        return "Competition"


class Dataset(TimestampMixin, PublishableMixin, db.Model):
    """A public dataset published by ADHAYAN (e.g. on Kaggle or Zenodo)."""

    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(400), default="", nullable=False)
    description = db.Column(db.Text, default="", nullable=False)  # Markdown
    source = db.Column(db.String(80), default="Kaggle", nullable=False)
    source_url = db.Column(db.String(400), default="", nullable=False)
    license = db.Column(db.String(120), default="", nullable=False)
    size_label = db.Column(db.String(80), default="", nullable=False)
    tags = db.Column(db.String(300), default="", nullable=False)  # comma list
    cover_image = db.Column(db.String(500), default="", nullable=False)
    meta_description = db.Column(db.String(300), default="", nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False, index=True)

    @property
    def tag_list(self) -> list[str]:
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]


class Publication(TimestampMixin, PublishableMixin, db.Model):
    """A research paper submitted by a member (Zenodo-style record)."""

    __tablename__ = "publications"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    author_name = db.Column(db.String(160), default="", nullable=False)
    member_id = db.Column(
        db.Integer, db.ForeignKey("members.id"), nullable=True, index=True
    )
    abstract = db.Column(db.Text, default="", nullable=False)
    keywords = db.Column(db.String(300), default="", nullable=False)  # comma list
    doi = db.Column(db.String(120), default="", nullable=False)
    license = db.Column(db.String(120), default="CC BY 4.0", nullable=False)
    pdf_path = db.Column(db.String(300), default="", nullable=False)  # relative path
    pdf_filename = db.Column(db.String(255), default="", nullable=False)
    pdf_size = db.Column(db.Integer, default=0, nullable=False)  # bytes
    github_url = db.Column(db.String(400), default="", nullable=False)
    dataset_url = db.Column(db.String(400), default="", nullable=False)
    software_language = db.Column(db.String(80), default="", nullable=False)
    software_status = db.Column(db.String(80), default="", nullable=False)
    references = db.Column(db.Text, default="", nullable=False)  # one per line
    meta_description = db.Column(db.String(300), default="", nullable=False)
    published_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    member = db.relationship("Member", backref=db.backref("publications", lazy="dynamic"))

    @property
    def publication_date_label(self) -> str:
        # The segmentation manuscript gives only a month, not an exact day.
        if (
            self.slug == "semantic-segmentation-autonomous-agricultural-robots"
            and self.published_at == datetime(2026, 7, 1)
        ):
            return "July 2026"
        return self.published_at.strftime("%B %d, %Y")

    @property
    def keyword_list(self) -> list[str]:
        return [k.strip() for k in (self.keywords or "").split(",") if k.strip()]

    @property
    def reference_list(self) -> list[str]:
        return [r.strip() for r in (self.references or "").split("\n") if r.strip()]

    @property
    def has_pdf(self) -> bool:
        return bool(self.pdf_path)

    @property
    def pdf_size_label(self) -> str:
        if not self.pdf_size:
            return ""
        mb = self.pdf_size / (1024 * 1024)
        if mb >= 1:
            return f"{mb:.1f} MB"
        return f"{max(1, round(self.pdf_size / 1024))} KB"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Publication {self.slug}>"


class SiteSetting(db.Model):
    """Key/value store for every editable string on the public site."""

    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, default="", nullable=False)
    label = db.Column(db.String(200), default="", nullable=False)
    group = db.Column(db.String(80), default="General", nullable=False, index=True)
    field_type = db.Column(db.String(20), default="text", nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    @staticmethod
    def get(key: str, default: str = "") -> str:
        row = SiteSetting.query.filter_by(key=key).first()
        return default if row is None else row.value

    @staticmethod
    def set(key: str, value: str, **kwargs) -> SiteSetting:
        row = SiteSetting.query.filter_by(key=key).first()
        if row is None:
            row = SiteSetting(key=key, **kwargs)
            db.session.add(row)
        row.value = value
        for extra_key, extra_value in kwargs.items():
            setattr(row, extra_key, extra_value)
        return row

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SiteSetting {self.key}>"


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(220), default="", nullable=False)
    inquiry_type = db.Column(db.String(60), default="general", nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
