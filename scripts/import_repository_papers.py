#!/usr/bin/env python3
"""Add the two bundled project papers without importing unrelated site content."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.repository_publications import import_repository_publications

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        created = import_repository_publications(db)
        db.session.commit()
        print(f"Added {created} project papers to research.")
