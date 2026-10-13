# Migration Report

Source: `peterkandel/AURA` (JSON content files) → ADHAYAN Flask/SQLite site.
Migration implemented in `app/seed.py`, invoked by `scripts/import_content.py`.
**Idempotent:** every record is matched on slug and skipped when it already
exists, so re-running never duplicates rows or overwrites admin edits.

## Summary

| Collection | Source records | Migrated | Skipped | Notes |
| --- | ---: | ---: | ---: | --- |
| Cofounders | 9 (+1) | 10 | 0 | 9 from `founders.json`; Prashanna Tiwari added from the organisation's founding declaration (founding member, listed in the seeded "Founding Declaration" post) with a supplied biography and local portrait |
| National heads | 4 | 4 | 0 | 2 people also cofounders — separate group records, shared portrait |
| News announcements | 1 | 1 | 0 | Published date, byline and body preserved |
| Opportunities | 0 | 0 | — | Source array was empty |
| Projects | 0 explicit | 7 | 0 | Derived strictly from named projects inside founder/head bios |
| Blog posts | 0 explicit | 2 | 0 | Organisation introduction + founding declaration, from the org's own documentation |
| Events/competitions | 1 (news item) | 1 | 0 | Weekly Competition 2 (Kaggle), dates/link preserved |
| Site settings | ~40 keys | 74 keys | 0 | Original copy + mission/vision/values + SEO fields |
| Media (logo) | 1 PNG | 3 files | 0 | Original PNG + optimised WebP + mark |
| Media (portraits) | 9 external URLs | 11 WebP files | 0 | postimg.cc URLs downloaded locally |

Run output (first execution):

```
Content import complete:
  settings         74 new record(s)
  team             13 new record(s)
  projects         7 new record(s)
  posts            2 new record(s)
  announcements    3 new record(s)
  events           0 new record(s)
  competitions     1 new record(s)
```

(Announcements = 1 from `news.json` + 2 organisation updates reconstructed
verbatim from the founding documentation that accompanies the original repo's
identity materials; both are dated and attributed to the founding team.)

Second run reports **0 new records** for every collection (verified by
`tests/test_seed.py::test_seed_is_idempotent`).

## Field-level mapping

> **Post-audit addition:** Prashanna Tiwari (cofounder, Nepal, sort order 15)
> was added after the initial audit, sourced from the organisation's own
> founding declaration and a supplied biography/portrait — not from the AURA
> JSON files. Team total is 14 (10 cofounders + 4 national heads).

### People (`founders.json`, `national_heads.json` → `team_members`)

| Source field | Destination | Transformation |
| --- | --- | --- |
| `id` | `slug` | Used directly where URL-safe; normalised otherwise (e.g. `peter_r_kandel` → `peter-r-kandel`) |
| `name` | `name` | Verbatim |
| `role` | `role` | Verbatim |
| `bio` | `bio` | Emoji/line-break formatting preserved (rendered with `br` filter) |
| `portrait_url` | `portrait` | Image downloaded; value now local `images/team/<slug>.webp` |
| `order` | `sort_order` | Preserved |
| `active` | `is_active` | Preserved |
| `country` (heads only) | `country` | Parsed from bio for cofounders |
| — | `group` | `cofounder` / `national_head` from source file |

External portrait URLs (attribution):
`i.postimg.cc` — PERU.jpg, Pakistan.jpg, Bangladesh.jpg, Ukraine.jpg,
Srilanka.jpg, Guinea.jpg, Nepal-1.jpg, Nepal-2.png, peter.jpg, india.jpg,
aus2.jpg. Converted to WebP, stored in `app/static/images/team/`.

### News (`news.json` → `announcements`)

| Source field | Destination | Transformation |
| --- | --- | --- |
| `id` | `slug` | Verbatim |
| `title` | `title` | Verbatim |
| `summary` | `summary` | Verbatim |
| `body` | `body` | CRLF → LF; Markdown link syntax applied to the bare Kaggle URL |
| `category` | `category` | Typo "Competition Announcment" corrected to "Competition Announcement" |
| `published_at` | `published_at` | Preserved (2026-10-12) |
| `byline` | — → blog-style credit in body | No `author` column on announcements; author named in body text |
| `image_url` | `image` | Empty in source; empty here |
| `published` / `featured` | `status` / `featured` | Mapped |

### Site copy (`site.json` → `site_settings`)

`organization_name`, `tagline`, `hero_title`, `hero_eyebrow`, `intro` and the
label keys map onto editable settings (`org_name`, `tagline`, `hero_title`,
`hero_eyebrow`, `intro_body`, …). Navigation labels were replaced by the new
information-architecture labels (About / Projects / Research / Team / News /
Events) — original values retained in this report for reference.

### Projects (derived from bios → `projects`)

| Project | Source mention | Slug |
| --- | --- | --- |
| NATERIDA | Peter R. Kandel bio ("award-winning robotics team project") | `naterida` |
| Flood victim tracking app | Peter R. Kandel bio | `flood-victim-tracking-app` |
| Transformer from scratch | Pitambar Lamichhane bio | `transformer-from-scratch` |
| ADHAYAN Weekly Competition 2 | Andrii Bilan / news.json | `adhayan-weekly-competition-2` |
| FIFA Data Exploration & Insights | Huzaifa Gulzar Shaikh bio | `fifa-data-exploration` |
| YOLOv11 posture recognition | Huzaifa Gulzar Shaikh bio | `yolov11-posture-recognition` |
| HealStream, C-Effect & Aeolian Nexus | Chanitha Sendinu Denagama bio | `healstream-c-effect-aeolian-nexus` |

Descriptions contain **only** what the source bios state — no invented
benchmarks, dates or results.

## Broken references / manual review

| Item | Status |
| --- | --- |
| All 11 postimg.cc portrait URLs | ✅ Downloaded successfully; no broken images |
| Kaggle competition URL | ✅ Preserved as demo/registration link |
| Contact e-mail (bilan.a@academy.com.ua) | ⚠️ Personal address from a public announcement — retained inside the announcement body as published; not surfaced as the organisation contact |
| Official contact e-mail | ⬜ Left blank in settings until the organisation publishes one |
| LinkedIn company page | ✅ Preserved (`linkedin_url` setting) |
| Original GitHub repository link | ✅ Preserved (`github_url` setting) |
| Original navigation label values | ℹ️ Replaced by new IA; originals recorded in this report |

## Redirect requirements

The original site's URL space (`/`, `/about`, `/news`, `/opportunities`,
`/news/<slug>`, `/opportunities/<slug>`) maps to the new site as:

| Old URL | New URL |
| --- | --- |
| `/` | `/` |
| `/about` | `/about` |
| `/news` | `/news` |
| `/news/<slug>` | `/news/<slug>` (slugs preserved) |
| `/opportunities` | `/events` (initiatives now under Events & Competitions) |
| `/opportunities/<slug>` | `/events` (no opportunity records existed) |

If the old domain stays live, add HTTP 301 rules for `/opportunities*` at the
hosting layer, or publish a single notice page.

## Verification

- Record counts before/after asserted in `tests/test_seed.py`.
- Re-run produces zero duplicates.
- Admin edits survive a re-run (regression-tested).
- Every founder name from the source JSON appears on the public team page.
