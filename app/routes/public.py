"""Public (visitor-facing) routes."""

from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from app.extensions import db
from app.models import (
    Announcement,
    BlogPost,
    Competition,
    ContactMessage,
    Event,
    Project,
    Publication,
    TeamMember,
)
from app.utils.helpers import send_email, setting

public_bp = Blueprint("public", __name__)


# --------------------------------------------------------------------------- home
@public_bp.route("/")
def index():
    projects = (
        Project.query.filter_by(status="published")
        .order_by(Project.featured.desc(), Project.sort_order, Project.id.desc())
        .limit(6)
        .all()
    )
    posts = (
        BlogPost.query.filter_by(status="published")
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )
    announcements = (
        Announcement.query.filter_by(status="published")
        .order_by(Announcement.published_at.desc())
        .limit(3)
        .all()
    )
    cofounders = (
        TeamMember.query.filter_by(is_active=True, group="cofounder")
        .order_by(TeamMember.sort_order, TeamMember.id)
        .all()
    )
    upcoming = _upcoming_items(limit=3)
    countries = _country_count()

    return render_template(
        "index.html",
        projects=projects,
        posts=posts,
        announcements=announcements,
        cofounders=cofounders,
        upcoming=upcoming,
        country_count=countries,
        cofounder_count=len(cofounders),
        page_title=setting("hero_title", "Where Curiosity Meets Innovation."),
        meta_description=setting("meta_home_description"),
    )


# -------------------------------------------------------------------------- about
@public_bp.route("/about")
def about():
    cofounders = (
        TeamMember.query.filter_by(is_active=True, group="cofounder")
        .order_by(TeamMember.sort_order, TeamMember.id)
        .all()
    )
    return render_template(
        "about.html",
        cofounders=cofounders,
        page_title=setting("about_page_title", "About ADHAYAN"),
        meta_description=setting("meta_about_description"),
    )


# ------------------------------------------------------------------------ projects
@public_bp.route("/projects")
def projects():
    query = Project.query.filter_by(status="published")

    category = request.args.get("category", "").strip()
    term = request.args.get("q", "").strip()

    categories = [
        row[0]
        for row in db.session.query(Project.category)
        .filter_by(status="published")
        .distinct()
        .order_by(Project.category)
        .all()
    ]

    if category:
        query = query.filter(Project.category == category)
    if term:
        like = f"%{term}%"
        query = query.filter(
            db.or_(
                Project.title.ilike(like),
                Project.summary.ilike(like),
                Project.description.ilike(like),
                Project.tech_stack.ilike(like),
                Project.category.ilike(like),
            )
        )

    items = query.order_by(Project.featured.desc(), Project.sort_order, Project.id.desc()).all()

    return render_template(
        "projects/index.html",
        projects=items,
        categories=categories,
        active_category=category,
        search_term=term,
        page_title=setting("projects_page_title", "Projects & Initiatives"),
        meta_description=setting("meta_projects_description"),
    )


@public_bp.route("/projects/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, status="published").first_or_404()
    related = (
        Project.query.filter(
            Project.status == "published",
            Project.id != project.id,
            Project.category == project.category,
        )
        .limit(2)
        .all()
    )
    return render_template(
        "projects/detail.html",
        project=project,
        related=related,
        page_title=project.title,
        meta_description=project.meta_description or project.summary,
    )


# ---------------------------------------------------------------------------- blog
@public_bp.route("/blog")
def blog():
    query = BlogPost.query.filter_by(status="published")
    category = request.args.get("category", "").strip()
    tag = request.args.get("tag", "").strip()

    categories = [
        row[0]
        for row in db.session.query(BlogPost.category)
        .filter_by(status="published")
        .distinct()
        .order_by(BlogPost.category)
        .all()
    ]

    if category:
        query = query.filter(BlogPost.category == category)
    if tag:
        query = query.filter(BlogPost.tags.ilike(f"%{tag}%"))

    posts = query.order_by(BlogPost.published_at.desc()).all()

    tags: list[str] = []
    for post in posts:
        for item in post.tag_list:
            if item not in tags:
                tags.append(item)

    return render_template(
        "blogs/index.html",
        posts=posts,
        categories=categories,
        tags=tags,
        active_category=category,
        active_tag=tag,
        page_title=setting("blog_page_title", "Blogs & Research"),
        meta_description=setting("meta_blog_description"),
    )


@public_bp.route("/blog/<slug>")
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, status="published").first_or_404()
    more = (
        BlogPost.query.filter(
            BlogPost.status == "published", BlogPost.id != post.id
        )
        .order_by(BlogPost.published_at.desc())
        .limit(2)
        .all()
    )
    return render_template(
        "blogs/detail.html",
        post=post,
        more=more,
        page_title=post.title,
        meta_description=post.meta_description or post.excerpt,
    )


# ------------------------------------------------------------------------ research
@public_bp.route("/research")
def research():
    from app.utils.members import current_member

    query = Publication.query.filter_by(status="published")
    term = request.args.get("q", "").strip()

    if term:
        like = f"%{term}%"
        query = query.filter(
            db.or_(
                Publication.title.ilike(like),
                Publication.author_name.ilike(like),
                Publication.abstract.ilike(like),
                Publication.keywords.ilike(like),
            )
        )

    publications = query.order_by(Publication.published_at.desc()).all()

    return render_template(
        "research/index.html",
        publications=publications,
        search_term=term,
        member=current_member(),
        page_title=setting("research_page_title", "Research"),
        meta_description=setting(
            "meta_research_description",
            "Independent research preprints shared through ADHAYAN.",
        ),
    )


@public_bp.route("/research/<slug>")
def research_detail(slug):
    from app.utils.members import current_member

    publication = Publication.query.filter_by(slug=slug, status="published").first_or_404()
    more = (
        Publication.query.filter(
            Publication.status == "published", Publication.id != publication.id
        )
        .order_by(Publication.published_at.desc())
        .limit(3)
        .all()
    )
    return render_template(
        "research/detail.html",
        publication=publication,
        more=more,
        member=current_member(),
        page_title=publication.title,
        meta_description=publication.meta_description or publication.abstract[:180],
    )


# ----------------------------------------------------------------------------- team
@public_bp.route("/team")
def team():
    members = (
        TeamMember.query.filter_by(is_active=True)
        .order_by(TeamMember.group, TeamMember.sort_order, TeamMember.id)
        .all()
    )
    cofounders = [m for m in members if m.group == "cofounder"]
    heads = [m for m in members if m.group == "national_head"]
    others = [m for m in members if m.group == "team"]

    return render_template(
        "team.html",
        cofounders=cofounders,
        heads=heads,
        others=others,
        country_count=_country_count(),
        page_title=setting("team_page_title", "Cofounders & Team"),
        meta_description=setting("meta_team_description"),
    )


# --------------------------------------------------------------------------- news
@public_bp.route("/news")
def news():
    category = request.args.get("category", "").strip()
    query = Announcement.query.filter_by(status="published")
    if category:
        query = query.filter(Announcement.category == category)

    categories = [
        row[0]
        for row in db.session.query(Announcement.category)
        .filter_by(status="published")
        .distinct()
        .order_by(Announcement.category)
        .all()
    ]
    items = query.order_by(Announcement.published_at.desc()).all()

    return render_template(
        "news/index.html",
        announcements=items,
        categories=categories,
        active_category=category,
        page_title=setting("news_page_title", "News & Announcements"),
        meta_description=setting("meta_news_description"),
    )


@public_bp.route("/news/<slug>")
def news_detail(slug):
    item = Announcement.query.filter_by(slug=slug, status="published").first_or_404()
    return render_template(
        "news/detail.html",
        item=item,
        page_title=item.title,
        meta_description=item.meta_description or item.summary,
    )


# -------------------------------------------------------------------------- events
@public_bp.route("/events")
def events():
    kind = request.args.get("type", "all")
    if kind not in {"all", "events", "competitions"}:
        kind = "all"

    now = datetime.utcnow()
    events_list = Event.query.all()
    competitions = Competition.query.all()
    items = list(events_list) + list(competitions)

    if kind == "events":
        items = [i for i in items if isinstance(i, Event)]
    elif kind == "competitions":
        items = [i for i in items if isinstance(i, Competition)]

    def sort_key(item):
        return (item.starts_at or now)

    upcoming = sorted([i for i in items if i.status == "upcoming"], key=sort_key, reverse=True)
    completed = sorted(
        [i for i in items if i.status != "upcoming"], key=sort_key, reverse=True
    )

    return render_template(
        "events.html",
        upcoming=upcoming,
        completed=completed,
        active_kind=kind,
        page_title=setting("events_page_title", "Events & Competitions"),
        meta_description=setting("meta_events_description"),
    )


# ------------------------------------------------------------------------- contact
@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    from app.forms import ContactForm

    form = ContactForm()
    if request.method == "POST" and form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            subject=form.subject.data.strip() or "Website enquiry",
            inquiry_type=form.inquiry_type.data,
            message=form.message.data.strip(),
        )
        db.session.add(message)
        db.session.commit()

        recipient = current_app.config.get("CONTACT_RECIPIENT") or current_app.config.get(
            "CONTACT_EMAIL", ""
        )
        if recipient:
            send_email(
                subject=f"[ADHAYAN contact] {message.subject}",
                body=(
                    f"From: {message.name} <{message.email}>\n"
                    f"Type: {message.inquiry_type}\n\n{message.message}"
                ),
                sender=message.email,
                recipients=[recipient],
            )

        return render_template(
            "contact.html",
            form=ContactForm(),
            sent=True,
            page_title=setting("contact_page_title", "Contact"),
            meta_description=setting("meta_contact_description"),
        )

    return render_template(
        "contact.html",
        form=form,
        sent=False,
        page_title=setting("contact_page_title", "Contact"),
        meta_description=setting("meta_contact_description"),
    )


# ------------------------------------------------------------------------ media/seo
@public_bp.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, max_age=31536000
    )


@public_bp.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {setting('site_url')}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@public_bp.route("/sitemap.xml")
def sitemap():
    base = setting("site_url") or current_app.config.get("SITE_URL", "").rstrip("/")
    if not base:
        base = request.url_root.rstrip("/")

    entries: list[tuple[str, str]] = [
        (url_for("public.index"), datetime.utcnow()),
        (url_for("public.about"), datetime.utcnow()),
        (url_for("public.projects"), datetime.utcnow()),
        (url_for("public.research"), datetime.utcnow()),
        (url_for("public.blog"), datetime.utcnow()),
        (url_for("public.team"), datetime.utcnow()),
        (url_for("public.news"), datetime.utcnow()),
        (url_for("public.events"), datetime.utcnow()),
        (url_for("public.contact"), datetime.utcnow()),
    ]

    for project in Project.query.filter_by(status="published").all():
        entries.append((url_for("public.project_detail", slug=project.slug), project.updated_at))
    for post in BlogPost.query.filter_by(status="published").all():
        entries.append((url_for("public.blog_detail", slug=post.slug), post.published_at))
    for pub in Publication.query.filter_by(status="published").all():
        entries.append((url_for("public.research_detail", slug=pub.slug), pub.published_at))
    for item in Announcement.query.filter_by(status="published").all():
        entries.append((url_for("public.news_detail", slug=item.slug), item.published_at))

    xml = render_template("sitemap.xml", base=base, entries=entries)
    return Response(xml, mimetype="application/xml")


# ---------------------------------------------------------------------------- misc
def _upcoming_items(limit: int = 3):
    now = datetime.utcnow()
    items = list(Event.query.all()) + list(Competition.query.all())
    items = [i for i in items if i.status == "upcoming"]
    items.sort(key=lambda i: i.starts_at or now)
    return items[:limit]


def _country_count() -> int:
    countries = {
        member.country.strip()
        for member in TeamMember.query.filter_by(is_active=True).all()
        if member.country and member.country.strip()
    }
    return len(countries)
