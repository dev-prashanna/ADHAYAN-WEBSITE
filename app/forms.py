"""WTForms used by the contact page and the admin dashboard."""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    URL,
    ValidationError,
)

from app.models import (
    EVENT_STATUSES,
    PUBLISH_STATES,
    BlogPost,
    Project,
)

IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "gif"]


def _slug_conflict(model):
    """Build a validator that rejects duplicate slugs (excluding one id)."""

    def _validate(form, field):
        if not field.data:
            return
        query = model.query.filter_by(slug=field.data)
        if getattr(form, "_obj_id", None):
            query = query.filter(model.id != form._obj_id)
        if query.first() is not None:
            raise ValidationError("This slug is already in use.")

    return _validate


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=160)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    inquiry_type = SelectField(
        "I want to",
        choices=[
            ("general", "Ask a general question"),
            ("collaboration", "Propose a collaboration"),
            ("research", "Discuss research"),
            ("partnership", "Explore a partnership"),
            ("media", "Media enquiry"),
        ],
        default="general",
    )
    subject = StringField("Subject", validators=[Optional(), Length(max=220)])
    message = TextAreaField(
        "Message", validators=[DataRequired(), Length(min=10, max=5000)]
    )
    website = StringField("Website", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Send message")

    def validate_website(self, field):  # honeypot – humans never fill this in
        if field.data:
            raise ValidationError("Invalid submission.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = StringField("Password", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("Sign in")


class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    slug = StringField(
        "Slug",
        validators=[Optional(), Length(max=160), _slug_conflict(Project)],
        description="Leave blank to generate from the title.",
    )
    summary = StringField("Summary", validators=[Optional(), Length(max=400)])
    description = TextAreaField("Description (Markdown)", validators=[Optional()])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    tech_stack = StringField("Technology stack", validators=[Optional(), Length(max=400)])
    contributors = StringField("Contributors", validators=[Optional(), Length(max=400)])
    github_url = StringField("GitHub link", validators=[Optional(), URL(), Length(max=400)])
    demo_url = StringField("Demo link", validators=[Optional(), URL(), Length(max=400)])
    meta_description = StringField(
        "Meta description", validators=[Optional(), Length(max=300)]
    )
    status = SelectField("Status", choices=PUBLISH_STATES, default="published")
    featured = BooleanField("Feature on the homepage")
    sort_order = StringField("Sort order", validators=[Optional(), Length(max=10)])
    cover_image = StringField("Cover image path", validators=[Optional(), Length(max=300)])
    cover_image_upload = FileField(
        "Upload cover image",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Only PNG, JPG, WEBP or GIF files.")],
    )
    submit = SubmitField("Save project")


class BlogPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=220)])
    slug = StringField(
        "Slug",
        validators=[Optional(), Length(max=180), _slug_conflict(BlogPost)],
        description="Leave blank to generate from the title.",
    )
    excerpt = StringField("Excerpt", validators=[Optional(), Length(max=400)])
    content = TextAreaField("Content (Markdown)", validators=[Optional()])
    author = StringField("Author", validators=[Optional(), Length(max=160)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    tags = StringField("Tags", validators=[Optional(), Length(max=300)])
    meta_description = StringField(
        "Meta description", validators=[Optional(), Length(max=300)]
    )
    published_at = DateTimeLocalField(
        "Publish date", format="%Y-%m-%dT%H:%M", validators=[Optional()]
    )
    status = SelectField("Status", choices=PUBLISH_STATES, default="draft")
    featured = BooleanField("Feature on the homepage")
    cover_image = StringField("Cover image path", validators=[Optional(), Length(max=300)])
    cover_image_upload = FileField(
        "Upload cover image",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Only PNG, JPG, WEBP or GIF files.")],
    )
    submit = SubmitField("Save post")


class TeamMemberForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=160)])
    slug = StringField("Slug", validators=[Optional(), Length(max=160)])
    role = StringField("Role", validators=[Optional(), Length(max=160)])
    group = SelectField(
        "Group",
        choices=[
            ("cofounder", "Co-founder"),
            ("national_head", "National head"),
            ("team", "Team member"),
        ],
        default="cofounder",
    )
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    bio = TextAreaField("Biography", validators=[Optional()])
    skills = StringField("Skills / interests", validators=[Optional(), Length(max=400)])
    github_url = StringField("GitHub", validators=[Optional(), URL(), Length(max=400)])
    linkedin_url = StringField("LinkedIn", validators=[Optional(), URL(), Length(max=400)])
    website_url = StringField("Website", validators=[Optional(), URL(), Length(max=400)])
    sort_order = StringField("Sort order", validators=[Optional(), Length(max=10)])
    is_active = BooleanField("Visible on the website", default=True)
    featured = BooleanField("Feature on the homepage")
    portrait = StringField("Portrait path", validators=[Optional(), Length(max=300)])
    portrait_upload = FileField(
        "Upload portrait",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Only PNG, JPG, WEBP or GIF files.")],
    )
    submit = SubmitField("Save profile")


class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=220)])
    slug = StringField("Slug", validators=[Optional(), Length(max=180)])
    summary = StringField("Summary", validators=[Optional(), Length(max=400)])
    body = TextAreaField("Body (Markdown)", validators=[Optional()])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    meta_description = StringField(
        "Meta description", validators=[Optional(), Length(max=300)]
    )
    published_at = DateTimeLocalField(
        "Publish date", format="%Y-%m-%dT%H:%M", validators=[Optional()]
    )
    status = SelectField("Status", choices=PUBLISH_STATES, default="published")
    featured = BooleanField("Feature on the homepage")
    sort_order = StringField("Sort order", validators=[Optional(), Length(max=10)])
    image = StringField("Image path", validators=[Optional(), Length(max=300)])
    image_upload = FileField(
        "Upload image",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Only PNG, JPG, WEBP or GIF files.")],
    )
    submit = SubmitField("Save announcement")


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=220)])
    slug = StringField("Slug", validators=[Optional(), Length(max=180)])
    summary = StringField("Summary", validators=[Optional(), Length(max=400)])
    description = TextAreaField("Description (Markdown)", validators=[Optional()])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    starts_at = DateTimeLocalField("Starts", format="%Y-%m-%dT%H:%M", validators=[Optional()])
    ends_at = DateTimeLocalField("Ends", format="%Y-%m-%dT%H:%M", validators=[Optional()])
    location = StringField("Location", validators=[Optional(), Length(max=200)])
    mode = SelectField(
        "Mode",
        choices=[("online", "Online"), ("in_person", "In person"), ("hybrid", "Hybrid")],
        default="online",
    )
    registration_deadline = DateTimeLocalField(
        "Registration deadline", format="%Y-%m-%dT%H:%M", validators=[Optional()]
    )
    registration_url = StringField(
        "Registration link", validators=[Optional(), URL(), Length(max=400)]
    )
    status = SelectField("Status", choices=EVENT_STATUSES, default="upcoming")
    meta_description = StringField(
        "Meta description", validators=[Optional(), Length(max=300)]
    )
    sort_order = StringField("Sort order", validators=[Optional(), Length(max=10)])
    image = StringField("Image path", validators=[Optional(), Length(max=300)])
    image_upload = FileField(
        "Upload image",
        validators=[FileAllowed(IMAGE_EXTENSIONS, "Only PNG, JPG, WEBP or GIF files.")],
    )
    submit = SubmitField("Save")


class SettingsForm(FlaskForm):
    """CSRF-only marker form; each setting is read straight from ``request.form``
    by the admin route (see ``admin.edit_settings``) so the field set can change
    without rebuilding the form class."""

    submit = SubmitField("Save settings")
