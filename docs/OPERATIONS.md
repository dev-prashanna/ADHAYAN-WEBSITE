# Operations

Day-to-day running of the ADHAYAN website for the maintainer.

## Routine tasks

| Task | How |
| --- | --- |
| Edit content | `/admin` dashboard — see `docs/CMS_GUIDE.md` |
| Deploy a code change | `git push origin main` (Render auto-deploys; content on the disk is untouched) |
| Change environment variables | Render dashboard → service → Environment → Save (service restarts) |
| View contact messages | Admin → Messages |
| Rotate the admin password | `ADMIN_USERNAME=x ADMIN_PASSWORD=newpass python scripts/create_admin.py` locally, or create a temp user and delete the old one |

## Backups

Full procedures (manual + Render scheduled backups + restore) are in
`docs/DEPLOYMENT.md`. Minimum viable routine:

- Enable Render **scheduled disk backups**.
- Once a month, pull an off-platform copy of `/var/data/adhayan.db` via the
  Render shell (see Deployment §6) and store it somewhere that is not the
  Render disk (local machine, private S3 bucket, etc.).
- After any bulk content import or before a risky upgrade, take an extra
  manual snapshot.

## Restoring

1. Stop the service (Render → Suspend, or scale to zero).
2. Replace `/var/data/adhayan.db` (and `uploads/` if the backup includes it).
3. Start the service. If the backup predates a schema change, run
   `flask db upgrade` in the shell first.

## Dependency upgrades

```bash
pip install -U -r requirements.txt   # or bump pins deliberately, one by one
python -m pytest tests/ -q           # must stay green
npm outdated && npm update           # Tailwind tooling only
npm run build:css                    # rebuild committed CSS
git push origin main
```

Upgrade Python minor versions on Render by changing `PYTHON_VERSION` and
verifying a deploy. Review Render's build logs after every dependency bump.

## Schema changes

```bash
flask --app run db migrate -m "describe change"
flask --app run db upgrade          # local
git push origin main                # Render build command runs db upgrade
```

`scripts/init_db.py` (`create_all`) remains as a safety net for brand-new
databases only — never rely on it to alter an existing schema.

## Monitoring

- Uptime: any HTTP monitor against `/robots.txt` (no DB dependency).
- Errors: Render → service → Logs. The app logs warnings for undelivered
  contact e-mail and unexpected exceptions appear as 500s with a generic page.
- Disk usage: Render → service → Metrics (uploads + DB). 1 GB covers years of
  text content; raise the disk size if large images accumulate.

## Content audit trail

The application does not keep full revision history. Operational safeguards:

- Backups are the undo mechanism for destructive edits/deletes.
- Drafts (`status=draft`) are the safety net for unpublished work.
- Slug changes break old URLs — search the sitemap before renaming a
  published slug.

## Incident checklist

1. **Site down** → check Render deploy status and logs; roll back to the
   previous deploy in Render if a release caused it.
2. **Data lost / corrupted** → restore the latest disk backup (above); keep
   the damaged `adhayan.db` aside for inspection.
3. **Admin account locked out** (rate limiter) → wait 5 minutes, or restart
   the service to clear the in-memory counter.
4. **Spam contact messages** → delete in Admin → Messages; consider tightening
   validation or adding a mail-filtering provider in front of SMTP.
5. **Suspected compromise** → rotate `SECRET_KEY` (invalidates all sessions),
   reset the admin password, review Admin → Messages and Render logs, check
   the `users` table for unexpected accounts.

## Ownership handover

Everything a new maintainer needs:

1. This file + `docs/DEPLOYMENT.md` + `docs/CMS_GUIDE.md`
2. Render account access (service + disk + env vars)
3. GitHub repository access
4. Domain registrar access (DNS)
5. Latest off-platform database backup
6. Admin credentials (delivered out-of-band, changed on receipt)
