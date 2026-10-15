"""Google sign-in, member applications and research-paper uploads.

Members authenticate with Google (Authlib) and are tracked in the Flask
session, keeping the administrator login on Flask-Login completely separate.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from authlib.integrations.flask_client import OAuth

from app.extensions import db
from app.forms import JoinForm, PublicationForm
from app.models import Member, Publication, utcnow
from app.utils.application_review import score_application
from app.utils.helpers import send_email, unique_slug
from app.utils.members import (
    approved_member_required,
    current_member,
    login_member,
    logout_member,
)
from app.utils.uploads import UploadError, save_document

members_bp = Blueprint("members", __name__)

oauth = OAuth()
google = None  # registered in ``init_oauth`` when credentials are configured


def init_oauth(app) -> None:
    """Bind Authlib to the app and register Google when configured."""
    global google
    oauth.init_app(app)
    if app.config.get("GOOGLE_CLIENT_ID"):
        google = oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url=app.config.get("GOOGLE_DISCOVERY_URL"),
            client_kwargs={"scope": "openid email profile"},
        )


def _safe_next(target: str | None) -> str:
    """Only allow same-site redirect targets."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("public.research")


def _google_configured() -> bool:
    return google is not None


# ------------------------------------------------------------------ google oauth
@members_bp.route("/auth/google")
def google_login():
    member = current_member()
    if member is not None:
        return redirect(_safe_next(request.args.get("next")))

    if not _google_configured():
        flash(
            "Google sign-in is not configured yet. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET to enable it.",
            "warning",
        )
        return redirect(url_for("public.index"))

    # Remember where to send the user after signing in.
    next_target = request.args.get("next", "")
    if next_target.startswith("/") and not next_target.startswith("//"):
        session["oauth_next"] = next_target

    redirect_uri = url_for("members.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@members_bp.route("/auth/google/callback")
def google_callback():
    if not _google_configured():
        flash("Google sign-in is not configured.", "error")
        return redirect(url_for("public.index"))

    token = google.authorize_access_token()
    userinfo = token.get("userinfo")
    if not userinfo:
        try:
            userinfo = google.parse_id_token(token)
        except Exception:  # pragma: no cover - network dependent
            userinfo = google.userinfo(token=token)

    email = (userinfo.get("email") or "").strip().lower()
    if not email:
        flash("Google did not return an email address for this account.", "error")
        return redirect(url_for("public.index"))

    google_id = userinfo.get("sub") or ""
    name = (userinfo.get("name") or "").strip()
    avatar = (userinfo.get("picture") or "").strip()

    member = Member.query.filter_by(email=email).first()
    if member is None:
        member = Member(
            google_id=google_id or None,
            email=email,
            name=name,
            avatar_url=avatar,
        )
        db.session.add(member)
    else:
        if google_id:
            member.google_id = google_id
        if name and not member.name:
            member.name = name
        if avatar and not member.avatar_url:
            member.avatar_url = avatar
    db.session.commit()

    login_member(member)

    next_target = session.pop("oauth_next", "")
    if not member.is_approved:
        flash(f"Welcome, {member.name or member.email}. Submit your application to join.", "success")
        return redirect(url_for("members.join"))

    flash(f"Signed in as {member.name or member.email}.", "success")
    return redirect(_safe_next(next_target))


@members_bp.route("/account/logout", methods=["POST"])
def member_logout():
    logout_member()
    flash("You have been signed out.", "success")
    return redirect(url_for("public.index"))


# ---------------------------------------------------------------------- join form
@members_bp.route("/join", methods=["GET", "POST"])
def join():
    member = current_member()
    if member is None:
        flash("Please sign in with Google before applying.", "warning")
        return redirect(url_for("members.google_login", next=url_for("members.join")))

    if member.is_approved:
        flash("You are already a member.", "success")
        return redirect(url_for("members.account"))

    form = JoinForm(obj=member)
    if form.validate_on_submit():
        member.name = form.name.data.strip()
        member.email = form.email.data.strip().lower()
        member.application_essay = form.application_essay.data.strip()
        member.applied_at = utcnow()

        score, reason = score_application(member.application_essay)
        member.essay_score = score
        min_score = current_app.config.get("APPLICATION_MIN_SCORE", 7)

        if score is not None and score >= min_score:
            member.application_status = "approved"
            member.approved_at = utcnow()
            db.session.commit()
            flash("Welcome to ADHAYAN Research. You can now submit your work.", "success")
            return redirect(url_for("public.research"))

        if score is not None:
            member.application_status = "rejected"
            db.session.commit()
            send_email(
                subject="ADHAYAN Research — application update",
                body=(
                    f"Hi {member.name or member.email},\n\n"
                    "Thank you for applying to ADHAYAN Research.\n\n"
                    "Unfortunately we cannot approve your application this time. "
                    "Please try again with more curiosity — tell us what you "
                    "genuinely want to explore and why collaborating with others "
                    "matters to you.\n\n"
                    f"Application score: {score}/10\n"
                    f"Reviewer note: {reason}\n\n"
                    "— ADHAYAN Research\n"
                ),
                sender="research@adhayan.org",
                recipients=[member.email],
            )
            flash(
                "Sorry — your application was not approved this time. "
                "Please try again with more curiosity.",
                "warning",
            )
            return render_template(
                "join.html",
                form=form,
                member=member,
                rejected=True,
                page_title="Join ADHAYAN Research",
                meta_description="Apply to join the ADHAYAN research network.",
            )

        # Scoring unavailable (no Groq key / network error) — hold for manual review.
        member.application_status = "pending"
        db.session.commit()
        flash(
            "Your application has been received and will be reviewed shortly.",
            "success",
            )
        return redirect(url_for("public.research"))

    return render_template(
        "join.html",
        form=form,
        member=member,
        page_title="Join ADHAYAN Research",
        meta_description="Apply to join the ADHAYAN research network.",
    )


# ------------------------------------------------------------------------ account
@members_bp.route("/account")
@approved_member_required
def account():
    member = current_member()
    publications = (
        Publication.query.filter_by(member_id=member.id)
        .order_by(Publication.published_at.desc())
        .all()
    )
    return render_template(
        "account/index.html",
        member=member,
        publications=publications,
        page_title="Your research",
        meta_description="Your ADHAYAN research submissions.",
    )


@members_bp.route("/account/research/new", methods=["GET", "POST"])
@approved_member_required
def upload_research():
    member = current_member()
    form = PublicationForm()
    if form.validate_on_submit():
        upload = form.pdf_upload.data
        if not upload or not getattr(upload, "filename", ""):
            flash("Please attach the paper as a PDF.", "error")
            return render_template(
                "research/upload.html",
                form=form,
                member=member,
                page_title="Submit research",
            )

        try:
            pdf_path, pdf_name, pdf_size = save_document(upload, subfolder="papers")
        except UploadError as exc:
            flash(str(exc), "error")
            return render_template(
                "research/upload.html",
                form=form,
                member=member,
                page_title="Submit research",
            )

        publication = Publication(
            slug=unique_slug(Publication, form.title.data.strip()),
            title=form.title.data.strip(),
            author_name=member.name or member.email.split("@")[0],
            member_id=member.id,
            abstract=form.abstract.data.strip(),
            keywords=(form.keywords.data or "").strip(),
            doi=(form.doi.data or "").strip(),
            license=(form.license.data or "CC BY 4.0").strip(),
            pdf_path=pdf_path,
            pdf_filename=pdf_name,
            pdf_size=pdf_size,
            github_url=(form.github_url.data or "").strip(),
            dataset_url=(form.dataset_url.data or "").strip(),
            software_language=(form.software_language.data or "").strip(),
            software_status=(form.software_status.data or "").strip(),
            references=(form.references.data or "").strip(),
            status="published",
            published_at=utcnow(),
        )
        db.session.add(publication)
        db.session.commit()
        flash("Your independent research preprint is now available.", "success")
        return redirect(url_for("public.research_detail", slug=publication.slug))

    return render_template(
        "research/upload.html",
        form=form,
        member=member,
        page_title="Submit research",
        meta_description="Upload a research paper to ADHAYAN Research.",
    )
