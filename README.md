# ADHAYAN — Website

**Made by Prashanna Tiwari — October 15, 2026.** All rights reserved (see [`LICENSE`](LICENSE)).

The official public website and content-management system for **ADHAYAN**
(AI-Driven Hub for Advanced Youth and Academic Networking), a youth-driven
academic network connecting students, educators and researchers working in
artificial intelligence and related fields.

Built as a single, maintainable Flask application: server-rendered Jinja
templates, Tailwind CSS, and a SQLite database on a persistent disk. One
student developer can run, deploy and maintain the whole system.

## What is included

- **Public website** — homepage, about, project gallery, blogs & research,
  cofounders/team, news, events & competitions, contact form
- **Research repository** (`/research`) — searchable preprint board; approved
  members submit PDFs with abstract, keywords, DOI, code and dataset links
- **Member accounts** — Google OAuth sign-in (Authlib); applications ask
  *"What is your research interest, and why do you want to collaborate?"*
  and are scored 1–10 by a Groq-hosted LLM on curiosity and willingness to
  collaborate (scores ≥ 7 auto-approve; lower scores are rejected with an
  optional e-mail notification)
- **Admin dashboard** (`/admin`) — create, edit, publish and delete every piece
  of site content without touching code
- **Content seeded from the original ADHAYAN repository** — 9 cofounders,
  4 national heads, projects, blog posts, announcements and site copy migrated
  from the [AURA repository](https://github.com/peterkandel/AURA); see
  `docs/CONTENT_AUDIT.md` and `docs/MIGRATION_REPORT.md`
- **Security** — hashed passwords, CSRF protection, session cookies, login
  rate limiting, sanitised Markdown, upload validation, security headers
- **SEO** — sitemap.xml, robots.txt, Open Graph tags, editable meta descriptions

## Quickstart (local development)

Requires Python 3.11+ (3.12 recommended). Node.js is only needed if you want to
rebuild the CSS (a prebuilt `app/static/css/main.css` is committed).

```bash
# 1. virtual environment + dependencies
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. configuration
cp .env.example .env               # then edit SECRET_KEY, SITE_URL,
                                   # GOOGLE_CLIENT_ID/SECRET and GROQ_API_KEY

# 3. database, admin account, original content
python scripts/init_db.py          # create tables
python scripts/create_admin.py     # create the administrator (prompts for password)
python scripts/import_content.py   # import original ADHAYAN content (safe to rerun)

# 4. run
python run.py                      # http://127.0.0.1:5000
```

Sign in at <http://127.0.0.1:5000/admin/login>.

The content import also adds the six repositories pinned on
[dev-prashanna's GitHub profile](https://github.com/dev-prashanna), verified on
October 13, 2026. All six are featured on the homepage and listed first in the
project gallery. Descriptions, technology tags, and repository links are stored
in the CMS and can be edited under Admin → Projects. This is a saved snapshot;
changing GitHub pins does not automatically update the website.

For an existing installation, rerun `python scripts/import_content.py` to add
the projects. The untouched original NATERIDA entry is upgraded in place;
records edited in the admin dashboard are preserved.

### Rebuilding the CSS (optional)

The committed `app/static/css/main.css` is a full production build. After
editing templates or `tailwind.config.js`:

```bash
npm install
npm run build:css      # or: npm run watch:css during development
```

## Tests

```bash
python -m pytest tests/ -q
```

57 tests cover models, Markdown/XSS sanitisation, public routes, admin CRUD,
authentication, CSRF enforcement, upload validation and seed idempotency.
See `docs/TESTING.md`.

## Deployment (Render)

The intended production setup is **one Render web service + one persistent
disk** (SQLite and uploads live on the disk). A persistent disk requires a
**paid** Render instance (Starter or above) — the free tier has ephemeral
storage and data would be lost on every deploy.

```bash
# 1. push this repository to GitHub
# 2. Render → New → Blueprint → select the repo (uses render.yaml)
# 3. attach a persistent disk at /var/data (render.yaml declares it)
# 4. set environment variables in the Render dashboard:
#      SECRET_KEY (generate one), SITE_URL (your domain),
#      ADMIN_USERNAME / ADMIN_PASSWORD (first deploy only),
#      SESSION_COOKIE_SECURE=true
# 5. deploy — the build command runs migrations, creates tables,
#    bootstraps the admin and imports the original content
```

Full step-by-step instructions, backup and recovery procedures:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Administration

| Task | Where |
| --- | --- |
| Edit homepage copy, hero text, footer, SEO | Admin → Settings |
| Add/edit projects | Admin → Projects |
| Write blog posts & research articles (Markdown) | Admin → Posts |
| Manage cofounders & team | Admin → Team |
| Publish announcements | Admin → Announcements |
| Create events & competitions | Admin → Events / Competitions |
| Answer contact messages | Admin → Messages |
| Upload/manage images | Admin → Media |

A nontechnical editor can run the entire site from the dashboard.
See [`docs/CMS_GUIDE.md`](docs/CMS_GUIDE.md).

## Project layout

```text
adhayan/
├── app/
│   ├── __init__.py        # application factory, security headers, template filters
│   ├── config.py          # environment-driven configuration
│   ├── extensions.py      # db / login / migrate / csrf instances
│   ├── forms.py           # WTForms (contact + all admin forms)
│   ├── models.py          # SQLAlchemy models
│   ├── seed.py            # idempotent import of original ADHAYAN content
│   ├── routes/
│   │   ├── public.py      # visitor-facing pages, sitemap, robots, media
│   │   ├── admin.py       # authenticated CMS (CRUD for every collection)
│   │   └── auth.py        # login / logout with rate limiting
│   ├── templates/         # Jinja2 (public pages + admin dashboard)
│   ├── static/            # compiled CSS, JS, logos, team portraits
│   └── utils/             # slug/settings/email, Markdown sanitiser, uploads
├── scripts/
│   ├── init_db.py         # create tables
│   ├── create_admin.py    # bootstrap administrator
│   └── import_content.py  # migrate original repository content
├── migrations/            # Flask-Migrate (Alembic) schema versions
├── tests/                 # pytest suite
├── docs/                  # architecture, security, deployment, guides
├── render.yaml            # Render blueprint (web service + persistent disk)
├── run.py                 # dev server / gunicorn entry point
└── requirements.txt
```

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Design decisions, stack rationale |
| [`docs/CONTENT_AUDIT.md`](docs/CONTENT_AUDIT.md) | Inventory of the original repository |
| [`docs/MIGRATION_REPORT.md`](docs/MIGRATION_REPORT.md) | What was migrated and how |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Render setup, backups, recovery |
| [`docs/CMS_GUIDE.md`](docs/CMS_GUIDE.md) | Editor handbook for the dashboard |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Threat model and safeguards |
| [`docs/TESTING.md`](docs/TESTING.md) | Running and writing tests |
| [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Backups, upgrades, maintenance |

## License & content provenance

Copyright (c) **October 15, 2026 Prashanna Tiwari**. All rights reserved.
**Made by Prashanna Tiwari.**

This repository is released under a **proprietary all-rights-reserved
license** (see [`LICENSE`](LICENSE)). It is **not** open source. You may view
the code for personal study, but you may **not** copy, redeploy, rebrand,
redistribute, or use it as a template for another site.

**The "ADHAYAN" name, acronym, logos, and branding are protected.** Unauthorised
use of the name or logos constitutes trademark infringement. Removing or
altering the "Made by Prashanna Tiwari" attribution is prohibited.

Organisational copy, founder biographies, project descriptions and
announcements originate from the ADHAYAN team's own materials in the
[AURA repository](https://github.com/peterkandel/AURA) and are reproduced
with light formatting changes only. No biographies, achievements or statistics
were invented for this site.
