#!/usr/bin/env python3
"""Attach bundled covers to existing projects with blank cover images."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import Project
from app.project_covers import backfill_project_covers

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        changed = backfill_project_covers(Project)
        db.session.commit()
        print(f"Updated {changed} project covers.")
