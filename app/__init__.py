"""Application factory for the ADHAYAN website."""

from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, render_template, request

from app.config import Config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_object=None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_object or Config)

    Config.init_app(app)
    _ensure_folders(app)

    _register_extensions(app)
    _register_blueprints(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    _register_cli(app)

    return app


def _ensure_folders(app: Flask) -> None:
    app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401  (register mappings)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(models.User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for

        return redirect(url_for("auth.login", next=request.path))


def _register_blueprints(app: Flask) -> None:
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")


def _register_template_helpers(app: Flask) -> None:
    from app.utils.helpers import setting, settings
    from app.utils.markdown import render_markdown, sanitize_html

    from markupsafe import Markup

    @app.template_filter("markdown")
    def _markdown_filter(text):
        return Markup(render_markdown(text))

    @app.template_filter("safe_html")
    def _safe_html_filter(text):
        return Markup(sanitize_html(text))

    @app.template_filter("datefmt")
    def _datefmt(value, fmt: str = "%B %d, %Y"):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return value.strftime(fmt)

    @app.template_filter("yearonly")
    def _yearonly(value):
        return value.strftime("%Y") if value else ""

    @app.template_filter("paragraphs")
    def _paragraphs_filter(text):
        import re

        if not text:
            return []
        normalised = text.replace("\r\n", "\n").replace("\r", "\n")
        return [chunk.strip() for chunk in re.split(r"\n\s*\n", normalised) if chunk.strip()]

    @app.template_filter("br")
    def _br_filter(text):
        from markupsafe import Markup, escape

        if not text:
            return ""
        return Markup(str(escape(str(text))).replace("\r\n", "\n").replace("\n", "<br>"))

    @app.context_processor
    def inject_globals():
        from app.models import TeamMember

        site_settings = settings()
        base = (site_settings.get("site_url") or app.config.get("SITE_URL") or "").rstrip("/")
        return {
            "s": setting,
            "site_base": base,
            "settings": site_settings,
            "current_year": datetime.utcnow().year,
            "nav_team_count": TeamMember.query.filter_by(is_active=True).count(),
            "request_path": request.path,
        }


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500


def _register_security_headers(app: Flask) -> None:
    csp = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self'"
    )

    @app.after_request
    def apply_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        if request.path.startswith("/admin"):
            response.headers.setdefault("Cache-Control", "no-store")
        elif response.headers.get("Content-Type", "").startswith("text/html"):
            response.headers.setdefault("Cache-Control", "public, max-age=300")
        if app.config.get("ENV", "production") != "development" and not app.debug:
            response.headers.setdefault("Content-Security-Policy", csp)
        return response


def _register_cli(app: Flask) -> None:
    @app.cli.command("create-admin")
    def create_admin():
        """Create (or update) the administrator account."""
        import getpass

        from werkzeug.security import generate_password_hash

        from app.models import User

        username = os.environ.get("ADMIN_USERNAME", "admin").strip()
        password = os.environ.get("ADMIN_PASSWORD", "").strip()

        with app.app_context():
            db.create_all()
            user = User.query.filter_by(username=username).first()
            if user is None:
                if not password:
                    password = getpass.getpass("Password: ")
                user = User(username=username, email=os.environ.get("ADMIN_EMAIL") or None)
                user.set_password(password)
                db.session.add(user)
                print(f"Created administrator '{username}'.")
            elif password:
                user.password_hash = generate_password_hash(password)
                print(f"Updated password for '{username}'.")
            else:
                print(f"Administrator '{username}' already exists.")
            db.session.commit()
