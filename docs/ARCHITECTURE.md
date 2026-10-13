# Architecture

## Summary

ADHAYAN is a **single Flask application** serving both the public website and
an authenticated content-management dashboard, backed by **SQLite** on a
persistent disk. Server-rendered Jinja2 templates with Tailwind CSS keep the
stack small enough for one student developer to own end-to-end.

```
Browser ──► Gunicorn ──► Flask (app factory)
                            ├── public blueprint   (/ , /projects, /blog, …)
                            ├── auth blueprint     (/admin/login, /admin/logout)
                            └── admin blueprint    (/admin/*, login-required)
                                     │
                              SQLAlchemy
                                     │
                              SQLite (DATA_DIR/adhayan.db)
                              Uploads (DATA_DIR/uploads/)
```

## Why this stack (vs. the alternatives considered)

The original AURA repository used Flask with a GitHub-backed JSON "CMS":
content lived in JSON files that a GitHub token committed back to the repo.
Two options were evaluated:

| Criterion | Option A: Flask + Git-backed JSON (original) | Option B: Flask + SQLite CMS (chosen) | Option C: Next.js + headless CMS |
| --- | --- | --- | --- |
| Editorial usability | Poor — edits become Git commits; needs a write token | Good — web forms, live in seconds | Good |
| Operating cost | Free (GitHub only) | Free / ~$7/mo Render with disk | $25+ (host + DB + CMS) |
| Media storage | Awkward (images in repo or external host) | Native uploads on the same disk | Object storage required |
| Search & relations | Manual, file-by-file | Real queries, filters, joins | Real queries |
| Deployment reliability | Keep-alive hacks needed for free tier | One service + one disk | Three services to manage |
| Maintenance surface | Custom persistence layer + secrets in CI | Ordinary Flask/SQLAlchemy | Node toolchain + external SaaS |
| Skill prerequisite | Python | Python | TypeScript + React + CMS admin |

**Decision: Option B.** The Git-backed CMS made every content edit a commit,
required a privileged GitHub token in the environment, and provided no usable
media pipeline. SQLite on a persistent disk gives real CRUD, filtering, and
uploads with almost no additional operational complexity, and stays within a
student budget (Render Starter ≈ $7/mo). Option C was rejected as
disproportionate for a content volume of tens of records and a one-person
maintainer.

## Key components

### Application factory (`app/__init__.py`)
Creates the Flask app from `Config`, wires extensions (SQLAlchemy, Flask-Login,
Flask-Migrate, Flask-WTF CSRF), registers blueprints, template filters
(`markdown`, `datefmt`, `paragraphs`, `br`), error handlers, security headers
(CSP, HSTS in production, nosniff, frame options), and the `create-admin` CLI.

### Configuration (`app/config.py`)
Everything environment-driven: `SECRET_KEY`, `DATA_DIR`, `UPLOAD_FOLDER`,
`DATABASE_URL`, `SITE_URL`, SMTP settings, cookie flags, login rate limits.
Local default: SQLite under `./instance/`. Production: `/var/data` on the
Render persistent disk. `TestConfig` swaps in in-memory SQLite.

### Data model (`app/models.py`)
Small, explicit tables: `User`, `Project`, `BlogPost`, `TeamMember`,
`Announcement`, `Event`, `Competition`, `SiteSetting`, `ContactMessage`.
Slug columns are unique and indexed; publish state is a `status` string
(`draft`/`published`); `SiteSetting` is a key/value store so every public
string is editable without code changes. Events and competitions share a
column set via an abstract `EventBase`.

### Content seeding (`app/seed.py`)
An idempotent importer holding the records extracted from the original AURA
repository (9 cofounders, 4 national heads, 7 projects, 2 posts, 3
announcements, 1 competition, ~74 site settings). Records are matched on slug
and skipped when present, so re-running never overwrites admin edits.
See `docs/MIGRATION_REPORT.md`.

### Public routes (`app/routes/public.py`)
Server-rendered pages; only `status="published"` rows are visible. Project
search uses SQL `LIKE`; category/tag filters are distinct-value queries.
Sitemap and robots.txt are generated from live data. Uploads are served from
`/media/<path>` with a one-year cache header.

### Admin (`app/routes/admin.py`)
One `before_request` hook guards the whole blueprint. Each collection
(projects, posts, team, announcements, events, competitions) has list, new,
edit and delete views sharing WTForms with server-side validation, optional
image uploads (validated by extension + Pillow, downscaled to ≤1920 px, saved
as WebP), and flash feedback. Settings are edited as grouped key/value rows.

### Authentication (`app/routes/auth.py`)
Single-admin (extendable) login with Werkzeug password hashing, HttpOnly
same-site session cookies, and an in-memory per-IP rate limiter
(default 8 attempts / 5 minutes).

### Markdown pipeline (`app/utils/markdown.py`)
Python-Markdown with tables, fenced code (Pygments), footnotes and TOC,
then **NH3 (Ammonia)** allow-list sanitisation — script tags, event handlers
and non-http(s)/mailto URLs are stripped, so admin-entered Markdown can never
inject XSS.

### Frontend
Prebuilt Tailwind CSS (`app/static/css/main.css`, 44 KB) with custom design
tokens (ink/mist/accent palette, Space Grotesk display, Inter body, JetBrains
Mono labels). One small vanilla-JS file for the mobile menu and scroll-reveal
classes. No client-side framework; progressive enhancement only.

## Data flow: publishing an article
1. Editor signs in at `/admin/login` (rate-limited, CSRF-protected).
2. Admin → Posts → New; writes Markdown, picks draft/published, optional cover.
3. `POST /admin/posts/new` validates the form, generates a unique slug,
   stores the row.
4. Public `/blog` and `/blog/<slug>` query `status="published"` only.
5. Sitemap/OG tags pick up the new record on the next request; public pages
   carry a 5-minute cache header, admin pages `no-store`.

## Scaling outlook
SQLite on one instance comfortably handles this site's read-heavy, low-write
workload into the tens of thousands of daily visitors. If growth demands more:
move `DATABASE_URL` to Postgres (SQLAlchemy makes this a connection-string
change plus a migration), and move uploads to S3-compatible storage. Neither
is needed at current scale, and neither is pre-built.
