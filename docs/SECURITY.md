# Security

## Threat model (what we defend against)

| Threat | Mitigation |
| --- | --- |
| Administrative account compromise | Werkzeug salted password hashing (scrypt), login rate limiting (8 attempts / 5 min / IP), session expiry (24 h), HttpOnly + SameSite cookies, optional Secure flag in production |
| XSS via Markdown/HTML content | All rendered Markdown and admin HTML passes through **NH3 (Ammonia)** allow-list sanitisation; script tags, event handlers, and `javascript:` URLs stripped; strict Content-Security-Policy in production |
| CSRF on admin or contact forms | Flask-WTF CSRF tokens on every POST form; global `CSRFProtect` rejects token-less mutations with HTTP 400 |
| Unauthorized content access | Whole `/admin` blueprint behind a `before_request` auth check; anonymous users redirected to login; server-side only (UI hiding is never the control) |
| Malicious file uploads | Extension allow-list (png/jpg/jpeg/webp/gif), Pillow decodes/validates real image data, ≤ 8 MB request ceiling, auto-downscale to ≤ 1920 px, stored outside code tree, served with fixed cache headers; path traversal in delete helper is neutralised by root-prefix check |
| Contact-form spam | Honeypot field (bots fill it → rejected), server-side WTForms validation, length limits, in-memory rate limiting on login |
| Credential leakage | `.env` git-ignored; `.env.example` has placeholders only; no secrets in templates or client JS; Render env vars; original repo's GitHub token was **not** carried over |
| Session fixation / cookie theft | Regenerated on login (Flask-Login), HttpOnly (no JS access), SameSite=Lax, Secure in production, HSTS header when Secure |
| Clickjacking | `X-Frame-Options: SAMEORIGIN` + CSP `frame-ancestors 'self'` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| Information disclosure in errors | Generic 404/500 templates; debug mode off in production; admin responses `Cache-Control: no-store` |
| Dependency vulnerabilities | Minimal dependency set (14 packages); standard, widely-audited libraries; upgrade via `requirements.txt` |

## Security headers (production)

Set in `app/__init__.py` after-request hook:

```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net;
  font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net;
  img-src 'self' data: https:; connect-src 'self'; object-src 'none';
  base-uri 'self'; form-action 'self'; frame-ancestors 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains   (when SESSION_COOKIE_SECURE)
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

`unsafe-inline` remains in `style-src` because Tailwind utility markup uses
inline `style` attributes sparingly and Jinja templates emit inline styles for
progressive-enhancement reveals; scripts are **not** allowed inline.

## Authentication model

- Single role in v1: any authenticated `User` may use the dashboard.
- Passwords stored as Werkzeug `scrypt` hashes (never reversible).
- Login route records failed attempts per client IP (honouring
  `X-Forwarded-For` on Render) and returns **429** once the limit is hit.
- Logout is POST-only and CSRF-protected.
- Extensible to multiple users/roles later (`User` table already per-row).

## Content sanitisation pipeline

```
Markdown ──python-markdown──► HTML ──nh3 allow-list──► safe HTML ──► template |markdown| filter
```

Allowed tags/attributes are explicitly enumerated in `app/utils/markdown.py`;
URL schemes limited to `http`, `https`, `mailto`. This runs on **render** (and
is covered by tests), so even a stored payload from an older client cannot
execute.

## Operational practices

- HTTPS everywhere in production (`SESSION_COOKIE_SECURE=true` + Render TLS).
- Secrets only via environment variables; rotate `SECRET_KEY` by regenerating
  (invalidates existing sessions — safe, users just re-login).
- Database and uploads on an access-controlled persistent disk; not in Git.
- Backups (see `docs/DEPLOYMENT.md`) enable point-in-time recovery.
- Contact messages stored in the database are visible only to admins; message
  bodies are never logged.

## Reporting

Found an issue? Contact the ADHAYAN team via the website contact form
(select "Media enquiry" or "General") before public disclosure.
