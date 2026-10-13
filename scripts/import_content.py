#!/usr/bin/env python3
"""Import the original ADHAYAN content into the database.

Safe to run as many times as you like: records are matched on their slug and
skipped when they already exist, so edits made in the admin dashboard are never
overwritten.

Usage:
    python scripts/import_content.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.seed import import_content  # noqa: E402


def main() -> int:
    app = create_app()
    with app.app_context():
        db.create_all()
        counts = import_content(db)
    print("Content import complete:")
    for name, value in counts.items():
        print(f"  {name:16s} {value} new record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
