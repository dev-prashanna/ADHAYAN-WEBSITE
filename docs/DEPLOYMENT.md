# Deployment

Target platform: **Render** — one web service (Python) + one **persistent
disk**. The SQLite database and all uploaded images live on that disk, so they
survive deploys and restarts.

> **Cost note.** Persistent disks are a **paid** Render feature (Starter plan
> and above, ≈ $7/month at time of writing). The Render free tier has
> ephemeral storage: a SQLite database placed there would be **deleted on
> every deploy and idle restart**. Do not run this application on the free
> tier and expect data to survive. If a free deployment is unavoidable,
> accept that all content must be re-imported each time (dev/demo only).

## 1. Prerequisites

- A GitHub repository containing this project
- A Render account
- (Optional) A domain name you control

## 2. Create the service

### Option A — Blueprint (recommended)

1. Render Dashboard → **New → Blueprint**.
2. Connect the GitHub repository; Render reads `render.yaml`.
3. Review the service definition; it declares:
   - Python 3.12 runtime, build & start commands
   - a 1 GB persistent disk mounted at `/var/data`
   - environment variables (some generated, some to fill in)
4. Create the blueprint.

### Option B — Manual web service

1. **New → Web Service** → connect the repo.
2. Runtime: Python · Branch: `main` · Instance: **Starter** (or higher).
3. Build command:
   ```bash
   pip install -r requirements.txt && python -m flask --app run db upgrade && python scripts/init_db.py && python scripts/import_content.py
   ```
4. Start command:
   ```bash
   gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60
   ```
5. **Disks → Add Disk**: name `adhayan-data`, mount path `/var/data`, 1 GB.
6. Add the environment variables below.

## 3. Environment variables

| Variable | Value | Notes |
| --- | --- | --- |
| `SECRET_KEY` | *(generated)* | Session/CSRF signing. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATA_DIR` | `/var/data` | SQLite + uploads live here |
| `UPLOAD_FOLDER` | `/var/data/uploads` | Uploaded images |
| `SITE_URL` | `https://your-domain.com` | Sitemap, canonical and OG URLs |
| `SESSION_COOKIE_SECURE` | `true` | Requires HTTPS (Render provides TLS) |
| `ADMIN_USERNAME` | e.g. `admin` | Used on first boot only |
| `ADMIN_PASSWORD` | *(strong password)* | Used on first boot only; unset after first deploy |
| `ADMIN_EMAIL` | optional | |
| `CONTACT_RECIPIENT` | optional | Inbox address for contact-form e-mail |
| `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USERNAME` / `MAIL_PASSWORD` | optional | SMTP delivery; omit to keep messages admin-inbox-only |

**After the first successful deploy, remove `ADMIN_PASSWORD` from the
environment** — the account already exists and the password is stored hashed.

## 4. First deploy

The build command is idempotent and performs, in order:

1. `pip install -r requirements.txt`
2. `flask db upgrade` — Alembic migrations (no-op on a fresh database)
3. `python scripts/init_db.py` — `create_all` safety net for fresh DBs
4. `python scripts/import_content.py` — bootstraps site settings + original
   ADHAYAN content; skips anything that already exists

After the deploy finishes, open the site, then sign in at
`https://your-domain.com/admin/login`.

## 5. Custom domain

Render → your service → **Settings → Domains** → add the domain, follow the
DNS instructions (CNAME for the `www`/app subdomain, plus an apex A/ALIAS if
required). Update `SITE_URL` to the final `https://` URL and redeploy (or
just save the env var — Render restarts the service).

## 6. Backups

The entire durable state is two paths on the disk:

- `/var/data/adhayan.db`
- `/var/data/uploads/`

### Automatic (recommended)

Render → your service → **Backups**. Paid instances support scheduled
database/disk backups with one-click restore.

### Manual via SSH

Render → your service → **Shell** (or `rssh`), then:

```bash
# snapshot the database (includes everything except binary uploads)
python - <<'PY'
import sqlite3, datetime
stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
src = sqlite3.connect("/var/data/adhayan.db")
dst = sqlite3.connect(f"/tmp/adhayan-backup-{stamp}.db")
src.backup(dst); dst.close(); src.close()
print("backup written")
PY

# download it from the shell with rsync/scp, or copy uploads too:
tar czf /tmp/adhayan-data.tgz -C /var/data adhayan.db uploads
```

Store backups off the Render disk (local machine, S3, GitHub private repo for
the DB dump only — **never** commit uploads or live DB to a public repo).

### Restore

1. Stop the service.
2. Replace `/var/data/adhayan.db` (and `uploads/` if needed) with the backup.
3. Start the service. No migrations are needed if the backup is from the
   current release; run `flask db upgrade` if restoring an older backup onto
   a newer release.

## 7. Updating the site

```bash
git push origin main
```

Render rebuilds and re-runs the idempotent build command. Because content now
lives in the disk's SQLite file (not in Git), a deploy never overwrites
editorial changes.

## 8. Costs (indicative, USD)

| Tier | Setup | Monthly |
| --- | --- | --- |
| Local / student laptop | $0 | $0 |
| Render Starter + 1 GB disk | — | ≈ $7 |
| Custom domain DNS | — | ≈ $0–15/yr |
| Transactional e-mail (optional, e.g. Resend/Brevo free tier) | $0 | $0 to start |
| **Realistic launch total** | — | **≈ $7–20/mo** |

Free-tier caveats, stated plainly: no persistent disk, cold starts, 500
build minutes/month, and services spin down after inactivity. This
application is designed for the paid Starter tier precisely because durable
SQLite storage is non-negotiable.

## 9. Health checks & monitoring

`render.yaml` sets `healthCheckPath: /robots.txt` (always 200, no DB needed).
For basic uptime monitoring point any HTTP monitor at `/robots.txt` or `/`.
