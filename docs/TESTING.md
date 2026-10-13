# Testing

## Running the suite

```bash
python -m pytest tests/ -q
```

On machines where a system Python exposes extra pytest plugins (e.g. ROS),
disable plugin autoload so only the project's tests run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q
```

Current status: **57 tests, all passing** (≈ 7 s).

## What is covered

| File | Scope |
| --- | --- |
| `tests/conftest.py` | Fixtures: in-memory-SQLite app, anonymous client, logged-in admin client, content seed |
| `tests/test_models.py` | Slug generation & uniqueness, password hashing, site-setting get/set, team skill parsing, event registration-open logic, tech-stack parsing |
| `tests/test_markdown.py` | Markdown → HTML (headings, tables, highlighted code), XSS vectors stripped (`<script>`, event handlers, `javascript:` URLs), safe links kept with `noopener`, iframes removed |
| `tests/test_public_routes.py` | Every public page returns 200; project/blog/news detail pages; 404s; project search & category filter; drafts hidden from public views; contact form stores messages; honeypot rejects bots; sitemap/robots; media route |
| `tests/test_admin.py` | Login required for `/admin`; login/logout; wrong password; project create→publish→edit→draft→delete round-trip; blog, team (incl. reorder), announcement, competition CRUD; settings propagate to the public homepage; duplicate slug rejected; dashboard stats; login rate limiting |
| `tests/test_security.py` | CSRF-enabled app: admin POST **without** token → 400 and no write; **with** token → succeeds; anonymous GET on admin routes redirects to login; regression test that delete forms embed a named `csrf_token` hidden input |
| `tests/test_seed.py` | Seed imports the expected record counts and all nine real founder names; second run inserts nothing; admin edits survive a re-run; all site-setting keys created |
| `tests/test_uploads.py` | Extension allow-list, real-image validation, missing file rejected, WebP conversion, large-image downscale, path-traversal-safe delete |

## Design notes

- The `app` fixture opens an app context for setup and **pops it before the
  test body**, so each `test_client` request receives a fresh app context and
  `flask.g` (matching production per-request contexts). This matters because
  site settings are request-cached on `g`.
- Ordinary form tests run with CSRF disabled for readability; the dedicated
  `test_security.py` module re-enables it to prove the control works.
- The login rate-limit test mutates `LOGIN_RATE_LIMIT` on the test config
  only.

## Adding tests

1. Use the `app` / `client` / `admin_client` / `seed` fixtures from
   `conftest.py`; create extra rows inside `with app.app_context():`.
2. Assert on status codes **and** on database state for write operations.
3. For anything touching rendered HTML, prefer checking a distinctive string
   you control (e.g. a slug you created) over layout markup.
4. Keep tests independent — each gets a brand-new in-memory database.

## Manual verification checklist (pre-release)

- [ ] `python -m pytest tests/ -q` — all green
- [ ] `npm run build:css` — CSS rebuilds cleanly
- [ ] `python run.py` — homepage, one project page, one article, team, news,
      events, contact all render on a phone-sized viewport
- [ ] Admin: create → preview (as anonymous tab) → publish → delete a draft
      project
- [ ] Contact form: submit once (appears in Admin → Messages); submit with the
      honeypot filled (rejected)
- [ ] `/sitemap.xml` and `/robots.txt` respond; `/admin` is disallowed
- [ ] Production build (`gunicorn run:app`) serves the same pages
