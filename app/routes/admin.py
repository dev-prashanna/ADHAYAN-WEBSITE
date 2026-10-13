"""Admin dashboard: every CRUD screen for the public website.

All routes in this blueprint are protected by the ``before_request`` hook below,
so a single check guards the whole ``/admin`` surface.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app.extensions import db
from app.forms import (
    AnnouncementForm,
    BlogPostForm,
    EventForm,
    ProjectForm,
    SettingsForm,
    TeamMemberForm,
)
from app.models import (
    Announcement,
    BlogPost,
    Competition,
    ContactMessage,
    Event,
    Project,
    SiteSetting,
    TeamMember,
)
from app.utils.helpers import unique_slug
from app.utils.uploads import UploadError, delete_image, save_image

admin_bp = Blueprint("admin", __name__)

MODEL_LABELS = {
    "projects": "Project",
    "posts": "Blog post",
    "team": "Team member",
    "announcements": "Announcement",
    "events": "Event",
    "competitions": "Competition",
}

COLLECTIONS = {
    "projects": ("Projects", "admin.project_new", "admin.project_edit", "admin.project_delete", "title"),
    "posts": ("Blog posts", "admin.post_new", "admin.post_edit", "admin.post_delete", "title"),
    "team": ("Team members", "admin.team_new", "admin.team_edit", "admin.team_delete", "name"),
    "announcements": ("Announcements", "admin.announcement_new", "admin.announcement_edit", "admin.announcement_delete", "title"),
    "events": ("Events", "admin.event_new", "admin.event_edit", "admin.event_delete", "title"),
    "competitions": ("Competitions", "admin.event_new", "admin.event_edit", "admin.event_delete", "title"),
}


def _collection_context(kind: str, items) -> dict:
    label, new_endpoint, edit_endpoint, delete_endpoint, name_field = COLLECTIONS[kind]
    kwargs = {"kind": kind} if kind in {"events", "competitions"} else {}
    return {
        "items": items,
        "kind": kind,
        "cfg": {
            "label": label,
            "new_url": url_for(new_endpoint, **kwargs),
            "edit_url": lambda item_id: url_for(edit_endpoint, item_id=item_id, **kwargs),
            "delete_url": lambda item_id: url_for(delete_endpoint, item_id=item_id, **kwargs),
            "name_field": name_field,
        },
    }


@admin_bp.before_request
def _require_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))


# ---------------------------------------------------------------------- dashboard
@admin_bp.route("/")
def dashboard():
    stats = {
        "projects": Project.query.count(),
        "posts": BlogPost.query.count(),
        "team": TeamMember.query.filter_by(is_active=True).count(),
        "announcements": Announcement.query.count(),
        "events": Event.query.count(),
        "competitions": Competition.query.count(),
        "messages": ContactMessage.query.count(),
        "unread": ContactMessage.query.filter_by(is_read=False).count(),
    }
    drafts = (
        Project.query.filter(Project.status != "published")
        .order_by(Project.updated_at.desc())
        .limit(5)
        .all()
    )
    drafts += [
        post
        for post in BlogPost.query.filter(BlogPost.status != "published")
        .order_by(BlogPost.updated_at.desc())
        .limit(5)
        .all()
    ]
    latest_messages = (
        ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        drafts=drafts,
        latest_messages=latest_messages,
    )


# ------------------------------------------------------------------------ projects
@admin_bp.route("/projects")
def projects_list():
    items = Project.query.order_by(Project.updated_at.desc()).all()
    return render_template("admin/collection.html", **_collection_context("projects", items))


@admin_bp.route("/projects/new", methods=["GET", "POST"])
def project_new():
    form = ProjectForm()
    if form.validate_on_submit():
        obj = Project()
        _populate_project(obj, form)
        obj.slug = unique_slug(Project, form.slug.data or form.title.data)
        db.session.add(obj)
        db.session.commit()
        flash("Project created.", "success")
        return redirect(url_for("admin.projects_list"))
    return render_template("admin/project_form.html", form=form, obj=None)


@admin_bp.route("/projects/<int:item_id>/edit", methods=["GET", "POST"])
def project_edit(item_id):
    obj = db.get_or_404(Project, item_id)
    form = ProjectForm(obj=obj)
    form._obj_id = obj.id
    if form.validate_on_submit():
        _populate_project(obj, form)
        slug = form.slug.data or obj.slug
        obj.slug = unique_slug(Project, slug, exclude_id=obj.id)
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("admin.projects_list"))
    return render_template("admin/project_form.html", form=form, obj=obj)


@admin_bp.route("/projects/<int:item_id>/delete", methods=["POST"])
def project_delete(item_id):
    obj = db.get_or_404(Project, item_id)
    delete_image(obj.cover_image)
    db.session.delete(obj)
    db.session.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("admin.projects_list"))


def _populate_project(obj: Project, form: ProjectForm) -> None:
    obj.title = form.title.data.strip()
    obj.summary = (form.summary.data or "").strip()
    obj.description = form.description.data or ""
    obj.category = (form.category.data or "Other").strip()
    obj.tech_stack = (form.tech_stack.data or "").strip()
    obj.contributors = (form.contributors.data or "").strip()
    obj.github_url = (form.github_url.data or "").strip()
    obj.demo_url = (form.demo_url.data or "").strip()
    obj.meta_description = (form.meta_description.data or "").strip()
    obj.status = form.status.data
    obj.featured = bool(form.featured.data)
    _apply_sort_order(obj, form.sort_order.data)
    _handle_upload(form, obj, "cover_image")


# ----------------------------------------------------------------------------- blog
@admin_bp.route("/posts")
def posts_list():
    items = BlogPost.query.order_by(BlogPost.updated_at.desc()).all()
    return render_template("admin/collection.html", **_collection_context("posts", items))


@admin_bp.route("/posts/new", methods=["GET", "POST"])
def post_new():
    form = BlogPostForm()
    if form.validate_on_submit():
        obj = BlogPost()
        _populate_post(obj, form)
        obj.slug = unique_slug(BlogPost, form.slug.data or form.title.data)
        db.session.add(obj)
        db.session.commit()
        flash("Blog post created.", "success")
        return redirect(url_for("admin.posts_list"))
    return render_template("admin/post_form.html", form=form, obj=None)


@admin_bp.route("/posts/<int:item_id>/edit", methods=["GET", "POST"])
def post_edit(item_id):
    obj = db.get_or_404(BlogPost, item_id)
    form = BlogPostForm(obj=obj)
    form._obj_id = obj.id
    if form.validate_on_submit():
        _populate_post(obj, form)
        obj.slug = unique_slug(BlogPost, form.slug.data or obj.slug, exclude_id=obj.id)
        db.session.commit()
        flash("Blog post updated.", "success")
        return redirect(url_for("admin.posts_list"))
    return render_template("admin/post_form.html", form=form, obj=obj)


@admin_bp.route("/posts/<int:item_id>/delete", methods=["POST"])
def post_delete(item_id):
    obj = db.get_or_404(BlogPost, item_id)
    delete_image(obj.cover_image)
    db.session.delete(obj)
    db.session.commit()
    flash("Blog post deleted.", "success")
    return redirect(url_for("admin.posts_list"))


def _populate_post(obj: BlogPost, form: BlogPostForm) -> None:
    obj.title = form.title.data.strip()
    obj.excerpt = (form.excerpt.data or "").strip()
    obj.content = form.content.data or ""
    obj.author = (form.author.data or "").strip()
    obj.category = (form.category.data or "Research").strip()
    obj.tags = (form.tags.data or "").strip()
    obj.meta_description = (form.meta_description.data or "").strip()
    obj.status = form.status.data
    obj.featured = bool(form.featured.data)
    if form.published_at.data:
        obj.published_at = form.published_at.data
    _handle_upload(form, obj, "cover_image")


# ------------------------------------------------------------------------ team
@admin_bp.route("/team")
def team_list():
    items = TeamMember.query.order_by(
        TeamMember.group, TeamMember.sort_order, TeamMember.id
    ).all()
    return render_template("admin/collection.html", **_collection_context("team", items))


@admin_bp.route("/team/new", methods=["GET", "POST"])
def team_new():
    form = TeamMemberForm()
    if form.validate_on_submit():
        obj = TeamMember()
        _populate_member(obj, form)
        obj.slug = unique_slug(TeamMember, form.slug.data or form.name.data)
        db.session.add(obj)
        db.session.commit()
        flash("Team member added.", "success")
        return redirect(url_for("admin.team_list"))
    return render_template("admin/team_form.html", form=form, obj=None)


@admin_bp.route("/team/<int:item_id>/edit", methods=["GET", "POST"])
def team_edit(item_id):
    obj = db.get_or_404(TeamMember, item_id)
    form = TeamMemberForm(obj=obj)
    form._obj_id = obj.id
    if form.validate_on_submit():
        _populate_member(obj, form)
        obj.slug = unique_slug(TeamMember, form.slug.data or obj.slug, exclude_id=obj.id)
        db.session.commit()
        flash("Team member updated.", "success")
        return redirect(url_for("admin.team_list"))
    return render_template("admin/team_form.html", form=form, obj=obj)


@admin_bp.route("/team/<int:item_id>/delete", methods=["POST"])
def team_delete(item_id):
    obj = db.get_or_404(TeamMember, item_id)
    delete_image(obj.portrait)
    db.session.delete(obj)
    db.session.commit()
    flash("Team member deleted.", "success")
    return redirect(url_for("admin.team_list"))


@admin_bp.route("/team/<int:item_id>/move/<direction>", methods=["POST"])
def team_move(item_id, direction):
    """Move a profile up or down inside its group and renumber the group."""
    obj = db.get_or_404(TeamMember, item_id)
    ordered = (
        TeamMember.query.filter_by(group=obj.group)
        .order_by(TeamMember.sort_order, TeamMember.id)
        .all()
    )
    index = [member.id for member in ordered].index(obj.id)
    target = index - 1 if direction == "up" else index + 1
    if 0 <= target < len(ordered):
        ordered[index], ordered[target] = ordered[target], ordered[index]
        for position, member in enumerate(ordered, start=1):
            member.sort_order = position * 10
        db.session.commit()
        flash("Order updated.", "success")
    else:
        flash("Already at the end of the list.", "error")
    return redirect(url_for("admin.team_list"))


def _populate_member(obj: TeamMember, form: TeamMemberForm) -> None:
    obj.name = form.name.data.strip()
    obj.role = (form.role.data or "").strip()
    obj.group = form.group.data
    obj.country = (form.country.data or "").strip()
    obj.bio = form.bio.data or ""
    obj.skills = (form.skills.data or "").strip()
    obj.github_url = (form.github_url.data or "").strip()
    obj.linkedin_url = (form.linkedin_url.data or "").strip()
    obj.website_url = (form.website_url.data or "").strip()
    _apply_sort_order(obj, form.sort_order.data)
    obj.is_active = bool(form.is_active.data)
    obj.featured = bool(form.featured.data)
    _handle_upload(form, obj, "portrait", subfolder="team")


# ------------------------------------------------------------------ announcements
@admin_bp.route("/announcements")
def announcements_list():
    items = Announcement.query.order_by(Announcement.updated_at.desc()).all()
    return render_template("admin/collection.html", **_collection_context("announcements", items))


@admin_bp.route("/announcements/new", methods=["GET", "POST"])
def announcement_new():
    form = AnnouncementForm()
    if form.validate_on_submit():
        obj = Announcement()
        _populate_announcement(obj, form)
        obj.slug = unique_slug(Announcement, form.slug.data or form.title.data)
        db.session.add(obj)
        db.session.commit()
        flash("Announcement created.", "success")
        return redirect(url_for("admin.announcements_list"))
    return render_template("admin/announcement_form.html", form=form, obj=None)


@admin_bp.route("/announcements/<int:item_id>/edit", methods=["GET", "POST"])
def announcement_edit(item_id):
    obj = db.get_or_404(Announcement, item_id)
    form = AnnouncementForm(obj=obj)
    form._obj_id = obj.id
    if form.validate_on_submit():
        _populate_announcement(obj, form)
        obj.slug = unique_slug(
            Announcement, form.slug.data or obj.slug, exclude_id=obj.id
        )
        db.session.commit()
        flash("Announcement updated.", "success")
        return redirect(url_for("admin.announcements_list"))
    return render_template("admin/announcement_form.html", form=form, obj=obj)


@admin_bp.route("/announcements/<int:item_id>/delete", methods=["POST"])
def announcement_delete(item_id):
    obj = db.get_or_404(Announcement, item_id)
    delete_image(obj.image)
    db.session.delete(obj)
    db.session.commit()
    flash("Announcement deleted.", "success")
    return redirect(url_for("admin.announcements_list"))


def _populate_announcement(obj: Announcement, form: AnnouncementForm) -> None:
    obj.title = form.title.data.strip()
    obj.summary = (form.summary.data or "").strip()
    obj.body = form.body.data or ""
    obj.category = (form.category.data or "Announcement").strip()
    obj.meta_description = (form.meta_description.data or "").strip()
    obj.status = form.status.data
    obj.featured = bool(form.featured.data)
    _apply_sort_order(obj, form.sort_order.data)
    if form.published_at.data:
        obj.published_at = form.published_at.data
    _handle_upload(form, obj, "image", subfolder="news")


# ------------------------------------------------------------- events/competitions
@admin_bp.route("/events")
def events_list():
    items = Event.query.order_by(Event.updated_at.desc()).all()
    return render_template("admin/collection.html", **_collection_context("events", items))


@admin_bp.route("/competitions")
def competitions_list():
    items = Competition.query.order_by(Competition.updated_at.desc()).all()
    return render_template("admin/collection.html", **_collection_context("competitions", items))


@admin_bp.route("/events/new", defaults={"kind": "events"}, methods=["GET", "POST"])
@admin_bp.route("/competitions/new", defaults={"kind": "competitions"}, methods=["GET", "POST"])
def event_new(kind):
    model = _event_model(kind)
    form = EventForm()
    if form.validate_on_submit():
        obj = model()
        _populate_event(obj, form)
        obj.slug = unique_slug(model, form.slug.data or form.title.data)
        db.session.add(obj)
        db.session.commit()
        flash(f"{MODEL_LABELS[kind]} created.", "success")
        return redirect(url_for("admin.events_list" if kind == "events" else "admin.competitions_list"))
    return render_template(
        "admin/event_form.html", form=form, obj=None, kind=kind, label=MODEL_LABELS[kind]
    )


@admin_bp.route("/events/<int:item_id>/edit", defaults={"kind": "events"}, methods=["GET", "POST"])
@admin_bp.route("/competitions/<int:item_id>/edit", defaults={"kind": "competitions"}, methods=["GET", "POST"])
def event_edit(kind, item_id):
    model = _event_model(kind)
    obj = db.get_or_404(model, item_id)
    form = EventForm(obj=obj)
    form._obj_id = obj.id
    if form.validate_on_submit():
        _populate_event(obj, form)
        obj.slug = unique_slug(model, form.slug.data or obj.slug, exclude_id=obj.id)
        db.session.commit()
        flash(f"{MODEL_LABELS[kind]} updated.", "success")
        return redirect(url_for("admin.events_list" if kind == "events" else "admin.competitions_list"))
    return render_template(
        "admin/event_form.html", form=form, obj=obj, kind=kind, label=MODEL_LABELS[kind]
    )


@admin_bp.route("/events/<int:item_id>/delete", defaults={"kind": "events"}, methods=["POST"])
@admin_bp.route("/competitions/<int:item_id>/delete", defaults={"kind": "competitions"}, methods=["POST"])
def event_delete(kind, item_id):
    model = _event_model(kind)
    obj = db.get_or_404(model, item_id)
    delete_image(obj.image)
    db.session.delete(obj)
    db.session.commit()
    flash(f"{MODEL_LABELS[kind]} deleted.", "success")
    return redirect(url_for("admin.events_list" if kind == "events" else "admin.competitions_list"))


def _event_model(kind: str):
    if kind == "events":
        return Event
    if kind == "competitions":
        return Competition
    from werkzeug.exceptions import NotFound

    raise NotFound()


def _populate_event(obj, form: EventForm) -> None:
    obj.title = form.title.data.strip()
    obj.summary = (form.summary.data or "").strip()
    obj.description = form.description.data or ""
    obj.category = (form.category.data or "").strip()
    obj.starts_at = form.starts_at.data
    obj.ends_at = form.ends_at.data
    obj.location = (form.location.data or "").strip()
    obj.mode = form.mode.data
    obj.registration_deadline = form.registration_deadline.data
    obj.registration_url = (form.registration_url.data or "").strip()
    obj.status = form.status.data
    obj.meta_description = (form.meta_description.data or "").strip()
    _apply_sort_order(obj, form.sort_order.data)
    _handle_upload(form, obj, "image", subfolder="events")


# ------------------------------------------------------------------------ messages
@admin_bp.route("/messages")
def messages_list():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/messages.html", items=items)


@admin_bp.route("/messages/<int:item_id>")
def message_detail(item_id):
    obj = db.get_or_404(ContactMessage, item_id)
    if not obj.is_read:
        obj.is_read = True
        db.session.commit()
    return render_template("admin/message_detail.html", item=obj)


@admin_bp.route("/messages/<int:item_id>/delete", methods=["POST"])
def message_delete(item_id):
    obj = db.get_or_404(ContactMessage, item_id)
    db.session.delete(obj)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("admin.messages_list"))


# ------------------------------------------------------------------------ settings
@admin_bp.route("/markdown-preview", methods=["POST"])
def markdown_preview():
    """Server-side Markdown → HTML preview used by the admin editor."""
    from app.utils.markdown import render_markdown

    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", ""))[:200_000]
    return {"html": render_markdown(text)}


@admin_bp.route("/settings", methods=["GET", "POST"])
def settings_page():
    rows = SiteSetting.query.order_by(SiteSetting.group, SiteSetting.sort_order).all()
    form = SettingsForm()
    if request.method == "POST" and form.validate_on_submit():
        updated = 0
        for row in rows:
            if row.key not in request.form and row.field_type != "boolean":
                continue
            if row.field_type == "boolean":
                value = "1" if request.form.get(row.key) else "0"
            else:
                value = request.form.get(row.key, row.value)
            if row.field_type == "url" and value and not _valid_url(value):
                flash(f"Skipped '{row.label or row.key}': not a valid URL.", "error")
                continue
            if row.value != value:
                row.value = value
                updated += 1
        db.session.commit()
        flash(f"Settings saved ({updated} change(s)).", "success")
        return redirect(url_for("admin.settings_page"))

    groups: dict[str, list] = {}
    for row in rows:
        groups.setdefault(row.group, []).append(row)
    return render_template("admin/settings.html", form=form, groups=groups)


@admin_bp.route("/settings/reset", methods=["POST"])
def settings_reset():
    """Re-run the content importer defaults (non-destructive for records)."""
    from app.seed import apply_default_settings

    apply_default_settings(db)
    db.session.commit()
    flash("Default copy restored. Content records were not touched.", "success")
    return redirect(url_for("admin.settings_page"))


# -------------------------------------------------------------------------- media
@admin_bp.route("/media")
def media_list():
    root = Path(current_app.config["UPLOAD_FOLDER"])
    files = []
    if root.exists():
        for path in sorted(root.rglob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                files.append(
                    {
                        "path": rel,
                        "url": url_for("public.media", filename=rel),
                        "size": path.stat().st_size,
                        "mtime": datetime.fromtimestamp(path.stat().st_mtime),
                    }
                )
    return render_template("admin/media.html", files=files[:300])


@admin_bp.route("/media/delete", methods=["POST"])
def media_delete():
    relative = request.form.get("path", "")
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = (root / relative).resolve()
    if not str(target).startswith(str(root)) or not target.is_file():
        flash("File not found.", "error")
        return redirect(url_for("admin.media_list"))
    target.unlink()
    flash("File deleted.", "success")
    return redirect(url_for("admin.media_list"))


# ------------------------------------------------------------------------- helpers
def _handle_upload(form, obj, field_name: str, subfolder: str = "images") -> None:
    upload = getattr(form, f"{field_name}_upload").data
    if upload and getattr(upload, "filename", ""):
        try:
            path = save_image(upload, subfolder)
        except UploadError as exc:
            flash(str(exc), "error")
            return
        current_value = getattr(obj, field_name, "")
        if current_value and current_value != path:
            delete_image(current_value)
        setattr(obj, field_name, path)


def _to_int(value, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _apply_sort_order(obj, value) -> None:
    if value not in (None, ""):
        obj.sort_order = _to_int(value, default=0)
    if obj.sort_order is None:
        obj.sort_order = 0
