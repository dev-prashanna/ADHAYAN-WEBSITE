"""Session helpers for Google-signed-in members.

Members are stored in their own table and tracked through the Flask session
(``member_id``) so the administrator login built on Flask-Login is untouched.
"""

from __future__ import annotations

from functools import wraps

from flask import flash, redirect, request, session, url_for

from app.extensions import db
from app.models import Member

SESSION_KEY = "member_id"


def current_member() -> Member | None:
    """Return the signed-in member, or ``None``."""
    member_id = session.get(SESSION_KEY)
    if not member_id:
        return None
    return db.session.get(Member, member_id)


def login_member(member: Member) -> None:
    session[SESSION_KEY] = member.id
    session.permanent = True


def logout_member() -> None:
    session.pop(SESSION_KEY, None)


def member_required(view):
    """Require any signed-in member."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_member() is None:
            flash("Please sign in with Google to continue.", "warning")
            return redirect(url_for("members.google_login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def approved_member_required(view):
    """Require a signed-in member whose application has been approved."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        member = current_member()
        if member is None:
            flash("Please sign in with Google to continue.", "warning")
            return redirect(url_for("members.google_login", next=request.path))
        if not member.is_approved:
            flash("Please submit your application to access this area.", "warning")
            return redirect(url_for("members.join"))
        return view(*args, **kwargs)

    return wrapper
