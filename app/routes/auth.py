"""Administrator sign-in / sign-out."""

from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import LoginForm
from app.models import User
from app.utils.helpers import rate_limit_exceeded, record_attempt, reset_attempts

auth_bp = Blueprint("auth", __name__)


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    ip = _client_ip()
    if rate_limit_exceeded(ip):
        flash("Too many sign-in attempts. Please wait a few minutes and try again.", "error")
        return render_template("admin/login.html", form=LoginForm()), 429

    form = LoginForm()
    if form.validate_on_submit():
        record_attempt(ip)
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user is not None and user.is_active and user.check_password(form.password.data):
            reset_attempts(ip)
            login_user(user, remember=False)
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid username or password.", "error")
        if rate_limit_exceeded(ip):
            flash("Too many sign-in attempts. Please wait a few minutes.", "error")

    return render_template("admin/login.html", form=form)


@auth_bp.route("/admin/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
