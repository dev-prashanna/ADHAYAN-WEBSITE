"""Import bundled manuscripts from the owner's project repositories."""
from datetime import datetime
import json
from pathlib import Path
import shutil

from flask import current_app

RECORDS_PATH = Path(__file__).parent / "data" / "repository_publications.json"


def import_repository_publications(db):
    """Add missing records and serve bundled PDFs; preserve existing records."""
    from app.models import Publication

    created = 0
    for stored in json.loads(RECORDS_PATH.read_text()):
        record = dict(stored)
        record["published_at"] = datetime.fromisoformat(record["published_at"])
        if Publication.query.filter_by(slug=record["slug"]).first() is None:
            db.session.add(Publication(**record))
            created += 1
        source = Path(current_app.static_folder) / "research" / Path(record["pdf_path"]).name
        destination = Path(current_app.config["UPLOAD_FOLDER"]) / record["pdf_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copyfile(source, destination)
    db.session.flush()
    return created
