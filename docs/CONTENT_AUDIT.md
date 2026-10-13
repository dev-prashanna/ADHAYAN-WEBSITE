# Content Audit — Original AURA Repository

Source: <https://github.com/peterkandel/AURA> (cloned and inspected file-by-file;
the original repository was not modified).

## Repository architecture (as found)

| Aspect | Finding |
| --- | --- |
| Framework | Flask (single `app.py`) |
| Templates | Jinja2 (`templates/`) — landing, about, news, opportunities, admin screens |
| Persistence | Dual: JSON files in `content/` **and** SQLAlchemy/SQLite migrations for users & opportunities |
| CMS mechanism | `github_persistence.py` commits JSON edits back to GitHub using a write token |
| Content service | `content_service.py` reads/writes the JSON documents |
| Frontend CSS | Hand-written `static/site.css` |
| Tests | One file, `tests/test_app.py` |
| Deployment | `DEPLOYMENT.md` + a GitHub Actions keep-alive workflow (free-tier workaround) |
| Media | One static logo (`static/adhayan-logo.png`); founder portraits hot-linked from postimg.cc |

## Content inventory

| Source file | Content type | Records | Destination in new site | Migration status |
| --- | --- | --- | --- | --- |
| `content/people/founders.json` | Co-founders | **9** | Team page / `team_members` (group=`cofounder`) | ✅ Migrated (portraits downloaded → `static/images/team/`) |
| `content/people/national_heads.json` | National heads | **4** (2 overlap founders) | Team page / `team_members` (group=`national_head`) | ✅ Migrated |
| `content/news.json` | News announcements | **1** | News & Announcements / `announcements` | ✅ Migrated |
| `content/opportunities.json` | Initiatives | **0** (empty array) | — | ⬜ Nothing to migrate; opportunities CRUD exists for future use |
| `content/site.json` | Site copy, navigation, hero text | 1 document (~40 keys) | `site_settings` (hero, intro, labels) | ✅ Migrated as editable settings |
| `content/about.json` | About page | 1 document (placeholder only, `sections: []`) | `site_settings` (about/mission/vision) | ✅ Migrated; placeholder intro replaced by the org's own founding-declaration copy |
| `static/adhayan-logo.png` | Logo | 1 | `app/static/images/` (+ WebP mark) | ✅ Copied & optimised |
| `templates/`, `app.py` | Architecture reference | — | New Flask app | 🔁 Re-implemented (not copied) |

**Totals found: 9 cofounders · 4 national heads · 1 news item · 0 opportunities ·
1 logo · 0 projects · 0 blog posts · 0 events** — the original repository
contained no projects, articles or events; those collections in the new site
are seeded only with work explicitly listed in founder/national-head bios
(NATERIDA, flood-tracking app, transformer-from-scratch, FIFA exploration,
YOLOv11 posture, HealStream/C-Effect/Aeolian Nexus, weekly competition #2) and
with organisation-level posts taken verbatim from the founding documentation.

## Founder / head roster (verbatim names & roles)

**Co-founders (9):** Pitambar Lamichhane (Nepal) · Ayan Zeeshan (Pakistan) ·
Shaidozzaman Araf (Bangladesh) · Andrii Bilan (Ukraine) ·
Chanitha Sendinu Denagama (Sri Lanka) · Albert Rodrigo Alvarez Jove (Peru) ·
Aboubacar Bangoura (Guinea) · Prince Kumar Mandal (Nepal) ·
Peter R. Kandel (Nepal)

**National heads (4):** Ayan Zeeshan (Pakistan) · Huzaifa Gulzar Shaikh (India) ·
Peter R. Kandel (Nepal) · Serena Li (Australia)

Ayan Zeeshan and Peter R. Kandel appear in both source files; both roles are
preserved (separate records in separate groups, sharing the same portrait).

## Media handling

Founder portraits were hot-linked to postimg.cc in the original. They have been
downloaded, converted to WebP and stored locally in
`app/static/images/team/` so the new site has no third-party image dependency.
Original external URLs are retained in `docs/MIGRATION_REPORT.md` for
attribution.

## Sensitive material

The original repository's `.env.example` and deployment notes reference a
GitHub write token and admin credentials. **No credential, token or secret from
the original repository was copied into this project.** The new architecture
does not need a GitHub write token at all.

## Undocumented / unreferenced findings

- `Report.md` and `DEPLOYMENT.md` document the JSON/GitHub CMS design; both
  were read and are superseded by this project's `docs/`.
- The original `about.json` was still placeholder text ("will be published
  here"); no organisational history existed in the repo. The About page copy
  in the new site comes from the organisation's own founding declaration
  (dated 1 September 2026), not invented narrative.
- Opportunities JSON was an empty array — the original opportunities UI had
  nothing to show.
