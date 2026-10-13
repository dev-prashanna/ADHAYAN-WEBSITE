#!/usr/bin/env python3
"""Create all database tables (equivalent to `flask db upgrade` on a fresh DB).

Migrations remain the normal way to evolve the schema once the site is live.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402


def main() -> int:
    app = create_app()
    with app.app_context():
        db.create_all()
        print(f"Tables created in {app.config['SQLALCHEMY_DATABASE_URI']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
