#!/usr/bin/env python3
"""Create or update the administrator account.

Credentials come from the environment (ADMIN_USERNAME / ADMIN_PASSWORD) so no
secret is ever written to source control. If ADMIN_PASSWORD is unset you are
prompted for it.

Usage:
    python scripts/create_admin.py
    ADMIN_USERNAME=admin ADMIN_PASSWORD=... python scripts/create_admin.py
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import User  # noqa: E402


def main() -> int:
    app = create_app()
    username = os.environ.get("ADMIN_USERNAME", "admin").strip()
    password = os.environ.get("ADMIN_PASSWORD", "").strip()
    email = os.environ.get("ADMIN_EMAIL", "").strip() or None

    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username=username).first()
        if user is None:
            if not password:
                password = getpass.getpass(f"Password for '{username}': ")
                confirm = getpass.getpass("Repeat password: ")
                if password != confirm:
                    print("Passwords do not match.")
                    return 1
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            action = "Created"
        else:
            if password:
                user.set_password(password)
                action = "Updated password for"
            else:
                action = "Already exists:"
        db.session.commit()
        print(f"{action} administrator '{username}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
