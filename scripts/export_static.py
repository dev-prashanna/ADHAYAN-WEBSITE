"""Export the public site to static HTML for GitHub Pages."""
import os
import re
import shutil
from pathlib import Path

from app import create_app

BASE = "ADHAYAN-WEBSITE"  # GitHub Pages serves under /<repo>/
OUT = Path("_site")

app = create_app()
client = app.test_client()

# Static list pages
PAGES = [
    "/",
    "/about",
    "/projects",
    "/blog",
    "/team",
    "/news",
    "/events",
    "/contact",
]


def slug_from_model(model, slug_attr="slug"):
    return getattr(model, slug_attr, None)


def rewrite(html: str) -> str:
    """Prefix root-absolute URLs so they work under /ADHAYAN-WEBSITE/."""
    for attr in ("href", "src", "action", "poster"):
        html = re.sub(
            rf'({attr}=")/',
            rf'\1/{BASE}/',
            html,
        )
    # url(/static/...) inside inline CSS
    html = re.sub(r"url\((['\"]?)/", rf"url(\1/{BASE}/", html)
    return html


def save(url: str, out_path: Path):
    resp = client.get(url)
    if resp.status_code != 200:
        print(f"  SKIP {url} -> {resp.status_code}")
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(rewrite(resp.get_data(as_text=True)).encode("utf-8"))
    print(f"  OK   {url} -> {out_path}")
    return True


def url_to_file(url: str) -> Path:
    if url == "/":
        return OUT / "index.html"
    return OUT / url.strip("/") / "index.html"


print("Rendering pages...")
with app.app_context():
    # Collect dynamic slugs from DB
    from app.models import Project, BlogPost, Announcement

    dynamic = []
    for proj in Project.query.all():
        if proj.slug:
            dynamic.append(f"/projects/{proj.slug}")
    for post in BlogPost.query.all():
        if post.slug:
            dynamic.append(f"/blog/{post.slug}")
    # News reuses blog posts in this app
    for post in BlogPost.query.all():
        if post.slug:
            dynamic.append(f"/news/{post.slug}")

    for url in PAGES + dynamic:
        save(url, url_to_file(url))

# Copy static assets
src_static = Path("app/static")
dst_static = OUT / "static"
if dst_static.exists():
    shutil.rmtree(dst_static)
shutil.copytree(src_static, dst_static)
print(f"Copied static assets -> {dst_static}")

# Copy uploads -> /media/ (Flask /media/<path> route serves from UPLOAD_FOLDER)
src_uploads = Path("instance/uploads")
dst_media = OUT / "media"
if src_uploads.exists():
    if dst_media.exists():
        shutil.rmtree(dst_media)
    shutil.copytree(src_uploads, dst_media)
    print(f"Copied uploads -> {dst_media}")

# 404 page (GitHub Pages custom 404)
resp = client.get("/nonexistent-page-xyz")
if resp.status_code == 404:
    (OUT / "404.html").write_bytes(rewrite(resp.get_data(as_text=True)).encode("utf-8"))
    print("Wrote 404.html")

print(f"\nDone. Static site in {OUT.resolve()}")
