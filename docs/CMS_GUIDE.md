# CMS Guide — Editor Handbook

The dashboard lives at **`/admin`**. Everything the public website displays is
managed here — no coding, no Git, no server access required.

## Signing in

1. Go to `https://your-domain.com/admin/login`.
2. Enter your username and password.
3. Too many wrong attempts temporarily locks you out (a few minutes) — wait
   and try again, or ask the site administrator to reset your password:

   ```bash
   ADMIN_USERNAME=yourname ADMIN_PASSWORD=newpassword python scripts/create_admin.py
   ```

Sign out with the **Sign out** button at the bottom of the sidebar.

## Dashboard overview

`/admin/` shows collection counts (projects, posts, team, announcements,
events, competitions), unread contact messages, and any drafts that still
need attention.

## Editing the homepage & site copy

**Admin → Settings.** Every headline, paragraph, footer line, button label and
meta description on the public site is a setting, grouped by area:

- **Branding** — organisation name, tagline, LinkedIn/GitHub links, founding date
- **Homepage** — hero eyebrow/title/body, hero buttons, mission, vision, values,
  section headings, join call-to-action
- **About / Pages** — per-page titles and introductions
- **Footer** — footer blurb
- **SEO** — default and per-page meta descriptions

Change the text → **Save settings** → the public site updates immediately.
URL-type settings validate the format and skip invalid values with a message.
**Restore default copy** resets wording to the original seed (content records
are never touched).

## Projects

**Admin → Projects.**

- **+ New project** — title (required), slug (blank = generated from title),
  summary, Markdown description, category, technology stack (comma-separated),
  contributors, GitHub/demo links, cover image (upload or path), status
  (draft/published), "Feature on the homepage", sort order, meta description.
- Published projects appear in the gallery and can be filtered/searched.
- **Drafts** are invisible to visitors — use them to prepare work in advance.
- Delete asks for confirmation and removes the cover image.

## Blog posts & research articles

**Admin → Posts.**

Same workflow as projects, plus author, category, tags, excerpt and publish
date. The editor is **Markdown**: headings `#`, bold `**text**`, links
`[label](url)`, fenced code blocks with syntax highlighting:

    ```python
    def hello():
        print("hi")
    ```

Tables, images (`![alt](url)`), blockquotes and footnotes also work. Content
is sanitised automatically — unsafe HTML is stripped on save/render.

## Team (cofounders & national heads)

**Admin → Team.**

- Groups: Co-founder · National head · Team member. Only groups with members
  are shown on the public page.
- **↑ / ↓** buttons reorder profiles within their group.
- Uncheck **Visible on the website** to hide someone without deleting them.
- Portraits: upload (PNG/JPG/WEBP/GIF, auto-converted to WebP) or paste a path.

## Announcements (news)

**Admin → Announcements.** Title, summary, Markdown body, category, publish
date, featured flag. The three latest published items appear in the homepage
news section; everything published is listed under `/news`.

## Events & competitions

**Admin → Events** and **Admin → Competitions** share one form:

- Title, summary, Markdown description, category, cover image
- Start/end time, location, mode (online / in person / hybrid)
- Registration deadline and registration link (any external form — no built-in
  ticketing)
- Status: upcoming · completed · cancelled

Upcoming entries appear on the homepage and at the top of `/events`;
completed ones move to the archive below.

## Contact messages

**Admin → Messages.** Every contact-form submission lands here. Open a message
to read it, reply by e-mail, or delete it. If SMTP is configured
(`CONTACT_RECIPIENT`), the site also forwards a copy by e-mail.

## Media

**Admin → Media.** Lists files uploaded through the forms (stored under
`uploads/` on the server disk) with sizes and delete buttons. Images are
automatically downscaled (max 1920 px) and converted to WebP.

## Good to know

- **Autosave?** No — press the save button. Drafts are the safety net.
- **Slugs** are the URL (`/projects/my-project`). Changing a slug changes the
  URL; old links will 404 unless you add a redirect.
- **Deleting is permanent** — every delete asks for confirmation.
- **Nothing is hardcoded** — if a section is empty on the public site, create
  the first record for that collection and it will appear.
