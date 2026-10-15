"""Idempotent content seed.

The original content in this module is sourced from the ADHAYAN material in the
``peterkandel/AURA`` repository and the ADHAYAN IP & brand documentation:

* ``content/site.json``, ``content/about.json``, ``content/news.json``
* ``content/people/founders.json`` and ``content/people/national_heads.json``
* ``FOUNDING.md`` / ``FOUNDERS.md`` / ``BRAND.md`` / ``CONTRIBUTORS.md``

No biography, achievement or organisational fact is invented here: text is
either copied from those sources or lightly re-ordered for the new layout.

Running the seed twice is safe – records are matched on their slug and skipped
when they already exist, so admin edits are never overwritten.
GitHub project additions are sourced from the verified snapshot in
``app.pinned_projects``. The untouched legacy NATERIDA entry is upgraded once.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

from flask import current_app

from app.pinned_projects import PINNED_PROJECT_RECORDS

from app.models import (
    Announcement,
    BlogPost,
    Competition,
    Dataset,
    Event,
    Project,
    Publication,
    SiteSetting,
    TeamMember,
)

# --------------------------------------------------------------------- settings
# (key, value, label, group, field_type)
DEFAULT_SETTINGS: list[tuple[str, str, str, str, str]] = [
    # ---------------------------------------------------------------- branding
    ("org_name", "ADHAYAN", "Organisation name", "Branding", "text"),
    (
        "org_full_name",
        "AI-Driven Hub for Advanced Youth and Academic Networking",
        "Full form of ADHAYAN",
        "Branding",
        "text",
    ),
    ("tagline", "Learn. Connect. Create.", "Tagline", "Branding", "text"),
    ("founded_on", "September 1, 2026", "Established on", "Branding", "text"),
    ("founded_place", "Nepal", "Established in", "Branding", "text"),
    (
        "site_url",
        "http://localhost:5000",
        "Public site URL (used for sitemap/OG tags)",
        "Branding",
        "url",
    ),
    (
        "linkedin_url",
        "https://www.linkedin.com/company/adhayan/",
        "Official LinkedIn page",
        "Branding",
        "url",
    ),
    (
        "github_url",
        "https://github.com/peterkandel/AURA",
        "Official GitHub repository",
        "Branding",
        "url",
    ),
    # ------------------------------------------------------------------- hero
    (
        "hero_eyebrow",
        "AI-Driven Hub for Advanced Youth and Academic Networking",
        "Hero eyebrow",
        "Homepage",
        "text",
    ),
    (
        "hero_title",
        "Where Curiosity Meets Innovation.",
        "Hero headline",
        "Homepage",
        "text",
    ),
    (
        "hero_body",
        "ADHAYAN is a youth-driven academic network built to connect curious minds, "
        "expand access to meaningful learning, and turn ideas into action.",
        "Hero description",
        "Homepage",
        "textarea",
    ),
    ("hero_primary_label", "Explore initiatives", "Primary button label", "Homepage", "text"),
    ("hero_primary_url", "/projects", "Primary button link", "Homepage", "text"),
    ("hero_secondary_label", "About ADHAYAN", "Secondary button label", "Homepage", "text"),
    ("hero_secondary_url", "/about", "Secondary button link", "Homepage", "text"),
    (
        "intro_heading",
        "An organization for learning in action",
        "Introduction heading",
        "Homepage",
        "text",
    ),
    (
        "intro_body",
        "ADHAYAN is a youth-driven academic network built to connect curious minds, "
        "expand access to meaningful learning, and turn ideas into action.\r\n\r\n"
        "We bring together students, educators, researchers, and organizations to learn "
        "beyond the classroom through academic communities, competitions, research, "
        "mentorship, and collaboration.\r\n\r\n"
        "From discovering a new field to building something of your own, ADHAYAN creates "
        "the space, connections, and opportunities for young people to explore, create, "
        "and grow.",
        "Introduction copy",
        "Homepage",
        "textarea",
    ),
    ("mission_title", "Our Mission", "Mission heading", "Homepage", "text"),
    (
        "mission_body",
        "Establish a community that brings together researchers, students, developers, "
        "and innovators working in artificial intelligence and related fields from "
        "across the globe — and facilitate the exchange of research findings, "
        "methodologies, and insights among members of the international AI research "
        "community.",
        "Mission statement",
        "Homepage",
        "textarea",
    ),
    ("vision_title", "Our Vision", "Vision heading", "Homepage", "text"),
    (
        "vision_body",
        "Build a genuinely international initiative with active participation from "
        "individuals across multiple countries and regions — supporting emerging "
        "researchers and practitioners in AI through mentorship, collaboration "
        "opportunities, and shared resources.",
        "Vision statement",
        "Homepage",
        "textarea",
    ),
    ("values_eyebrow", "Founding objectives", "Values eyebrow", "Homepage", "text"),
    ("values_title", "What we stand for", "Values heading", "Homepage", "text"),
    (
        "value_1_title",
        "International research collaboration",
        "Value 1 title",
        "Homepage",
        "text",
    ),
    (
        "value_1_body",
        "Establish a community that brings together researchers, students, developers, "
        "and innovators working in artificial intelligence and related fields from "
        "across the globe.",
        "Value 1 description",
        "Homepage",
        "textarea",
    ),
    ("value_2_title", "Knowledge sharing", "Value 2 title", "Homepage", "text"),
    (
        "value_2_body",
        "Facilitate the exchange of research findings, methodologies, and insights "
        "among members of the international AI research community.",
        "Value 2 description",
        "Homepage",
        "textarea",
    ),
    ("value_3_title", "Capacity building", "Value 3 title", "Homepage", "text"),
    (
        "value_3_body",
        "Support emerging researchers and practitioners in AI through mentorship, "
        "collaboration opportunities, and shared resources.",
        "Value 3 description",
        "Homepage",
        "textarea",
    ),
    ("value_4_title", "Global community development", "Value 4 title", "Homepage", "text"),
    (
        "value_4_body",
        "Build a genuinely international initiative with active participation from "
        "individuals across multiple countries and regions.",
        "Value 4 description",
        "Homepage",
        "textarea",
    ),
    ("home_projects_eyebrow", "Selected work", "Projects section eyebrow", "Homepage", "text"),
    (
        "home_projects_title",
        "Featured projects",
        "Projects section heading",
        "Homepage",
        "text",
    ),
    ("home_blog_eyebrow", "Thinking out loud", "Blog section eyebrow", "Homepage", "text"),
    ("home_blog_title", "Blogs & research", "Blog section heading", "Homepage", "text"),
    (
        "home_news_eyebrow",
        "From the organization",
        "News section eyebrow",
        "Homepage",
        "text",
    ),
    ("home_news_title", "Latest news", "News section heading", "Homepage", "text"),
    ("home_team_eyebrow", "The people behind it", "Team eyebrow", "Homepage", "text"),
    ("home_team_title", "Meet the cofounders", "Team heading", "Homepage", "text"),
    ("home_events_eyebrow", "Take part", "Events eyebrow", "Homepage", "text"),
    (
        "home_events_title",
        "Upcoming events & competitions",
        "Events heading",
        "Homepage",
        "text",
    ),
    ("join_eyebrow", "Join our initiative", "Join eyebrow", "Homepage", "text"),
    ("join_title", "Bring your curiosity.", "Join heading", "Homepage", "text"),
    (
        "join_body",
        "ADHAYAN is built by students, educators and researchers who want to learn "
        "beyond the classroom. Follow our official channels to see open initiatives, "
        "competitions and collaboration calls.",
        "Join copy",
        "Homepage",
        "textarea",
    ),
    ("join_cta_label", "Follow on LinkedIn", "Join button label", "Homepage", "text"),
    # ------------------------------------------------------------------ about
    ("about_page_eyebrow", "ADHAYAN / ABOUT", "About eyebrow", "About", "text"),
    ("about_page_title", "About ADHAYAN", "About page title", "About", "text"),
    (
        "about_page_intro",
        "ADHAYAN is an international research and collaboration initiative focused on "
        "artificial intelligence and related fields, established in Nepal.",
        "About page introduction",
        "About",
        "textarea",
    ),
    ("history_title", "Our history", "History heading", "About", "text"),
    (
        "history_body",
        "September 1, 2026 — Founding meeting held in Nepal; ADHAYAN established by "
        "decision of the founding members, and the name “ADHAYAN” adopted and "
        "first used.\r\n\r\n"
        "September 2026 — The founding team begins international outreach, with initial "
        "communications and collaboration in Sri Lanka, Pakistan, Bangladesh, Papua New "
        "Guinea and Peru.\r\n\r\n"
        "October 2026 — Official ADHAYAN logo created and first used; the ADHAYAN GitHub "
        "repository created for organizational documentation; official LinkedIn page "
        "established.\r\n\r\n"
        "October 2026 — This website published as the public home of the initiative.",
        "History timeline (plain text, blank line = new paragraph)",
        "About",
        "textarea",
    ),
    (
        "research_interests",
        "Artificial Intelligence · Machine Learning · Mathematics · Computer Vision · "
        "Robotics · Neural Networks · Optimization · Data Science · Software Engineering · "
        "Computational Problem Solving · Accessible Technology",
        "Research interests",
        "About",
        "textarea",
    ),
    # ----------------------------------------------------------------- pages
    (
        "projects_page_title",
        "Projects & Initiatives",
        "Projects page title",
        "Pages",
        "text",
    ),
    (
        "projects_page_intro",
        "Selected work and open initiatives from the ADHAYAN community.",
        "Projects page introduction",
        "Pages",
        "textarea",
    ),
    (
        "blog_page_title",
        "Blogs & Research",
        "Blog page title",
        "Pages",
        "text",
    ),
    (
        "blog_page_intro",
        "Notes, write-ups and research from the people building ADHAYAN.",
        "Blog page introduction",
        "Pages",
        "textarea",
    ),
    ("team_page_title", "Cofounders & Team", "Team page title", "Pages", "text"),
    (
        "team_page_intro",
        "A youth-driven team spread across nine countries, connected by a shared "
        "interest in artificial intelligence and open learning.",
        "Team page introduction",
        "Pages",
        "textarea",
    ),
    (
        "news_page_title",
        "News & Announcements",
        "News page title",
        "Pages",
        "text",
    ),
    (
        "news_page_intro",
        "Announcements, milestones and updates from the organization.",
        "News page introduction",
        "Pages",
        "textarea",
    ),
    (
        "events_page_title",
        "Events & Competitions",
        "Events page title",
        "Pages",
        "text",
    ),
    (
        "events_page_intro",
        "Competitions, workshops and community events run by ADHAYAN.",
        "Events page introduction",
        "Pages",
        "textarea",
    ),
    ("contact_page_title", "Contact", "Contact page title", "Pages", "text"),
    (
        "contact_page_intro",
        "Questions, research ideas, partnerships and press — we would love to hear from you.",
        "Contact page introduction",
        "Pages",
        "textarea",
    ),
    (
        "contact_email",
        "",
        "Official contact e-mail (leave blank until it is published)",
        "Pages",
        "text",
    ),
    # ----------------------------------------------------------------- footer
    (
        "footer_blurb",
        "ADHAYAN — a youth-driven academic network connecting curious minds across "
        "borders through learning, research and collaboration.",
        "Footer blurb",
        "Footer",
        "textarea",
    ),
    # -------------------------------------------------------------------- seo
    (
        "meta_default_description",
        "ADHAYAN is an international research and collaboration initiative for young "
        "people working in artificial intelligence and related fields.",
        "Default meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_home_description",
        "Where curiosity meets innovation. ADHAYAN connects students, educators and "
        "researchers to learn beyond the classroom.",
        "Homepage meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_about_description",
        "About ADHAYAN — mission, vision, founding objectives and history.",
        "About meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_projects_description",
        "Projects and initiatives from the ADHAYAN community.",
        "Projects meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_blog_description",
        "Blogs and research write-ups from ADHAYAN members.",
        "Blog meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_team_description",
        "Meet the cofounders and national heads of ADHAYAN.",
        "Team meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_news_description",
        "News and announcements from ADHAYAN.",
        "News meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_events_description",
        "Upcoming events and competitions hosted by ADHAYAN.",
        "Events meta description",
        "SEO",
        "textarea",
    ),
    (
        "meta_contact_description",
        "Contact ADHAYAN with research, collaboration or press enquiries.",
        "Contact meta description",
        "SEO",
        "textarea",
    ),
]


# ------------------------------------------------------------------- team import
TEAM_RECORDS: list[dict] = [
    {
        "slug": "pitambar-lamichhane",
        "name": "Pitambar Lamichhane",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Nepal",
        "sort_order": 10,
        "skills": "Artificial Intelligence, Machine Learning, Mathematics",
        "portrait": "images/team/pitambar-lamichhane.webp",
        "bio": (
            "🇳🇵 Country: Nepal\n"
            "🤖 Focus: Artificial Intelligence, Machine Learning, Mathematics\n"
            "🏆 NOAI 2026: Rank 1 / National Champion\n"
            "🌎 IOAI 2026: Honourable Mention\n"
            "🇳🇵 National Team: Nepal, IOAI 2026\n"
            "🧠 Interests: Neural Networks, Optimization, AI Research\n"
            "💻 Projects: Transformer from scratch, algorithmic/computational projects\n"
            "🚀 Leadership: Co-founder of ADHAYAN\n"
            "📚 Research: Published research involving quantitative analysis and "
            "technology adoption"
        ),
    },
    {
        "slug": "prashanna-tiwari",
        "name": "Prashanna Tiwari",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Nepal",
        "sort_order": 15,
        "skills": "Artificial Intelligence, Machine Learning, Robotics, Mathematics, Physics",
        "portrait": "images/team/prashanna-tiwari.webp",
        "bio": (
            "I’m a student passionate about AI, Machine Learning, Robotics, Mathematics, "
            "and Physics, driven by a deep eagerness for science and a commitment to use "
            "technology to create meaningful impact in the world. I live for creating, "
            "experimenting, and innovating—whether it’s developing autonomous robots, "
            "exploring reinforcement learning, designing AI-guided platforms, or "
            "engineering intelligent sensing and navigation systems. My journey is fueled "
            "by curiosity, research, and a relentless drive to understand how intelligence "
            "can be built, optimized, and applied to solve real problems. I’m always "
            "excited to collaborate on transformative AI and robotics projects that push "
            "the boundaries of what’s possible and contribute to a better future."
        ),
    },
    {
        "slug": "ayan-zeeshan",
        "name": "Ayan Zeeshan",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Pakistan",
        "sort_order": 20,
        "skills": "Artificial Intelligence, computational problem-solving",
        "portrait": "images/team/ayan-zeeshan.webp",
        "bio": (
            "🇵🇰 Country: Pakistan\n"
            "🏫 School: Aitchison College, Lahore\n"
            "🤖 Field: Artificial Intelligence / computational problem-solving\n"
            "🌎 International competition: IOAI 2026\n"
            "🏅 Result: Honourable Mention\n"
            "📊 IOAI rank: 222nd\n"
            "🏛️ National team: Pakistan, 2026\n"
            "🧠 Training: 3-week intensive AI training camp at PIEAS"
        ),
    },
    {
        "slug": "shaidozzaman-araf",
        "name": "Shaidozzaman Araf",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Bangladesh",
        "sort_order": 30,
        "skills": "AI, Machine Learning, Software Engineering",
        "portrait": "images/team/shaidozzaman-araf.webp",
        "bio": (
            "🇧🇩 Country: Bangladesh\n"
            "📍 Location: Mymensingh, Bangladesh\n"
            "🤖 Focus: AI, Machine Learning, Software Engineering\n"
            "🏆 APOAI 2026: Gold Medal — Rank 5\n"
            "🥉 IOAI 2026: Bronze Medal — Rank 161\n"
            "🇧🇩 IOAI: Bangladesh national-team delegate\n"
            "💻 BdAIO 2025: National camper; Rank 7 in national round\n"
            "🧑‍💻 BOI 2025: National contestant\n"
            "🚀 Entrepreneurship: Co-Founder/CEO/CTO, Dead Mans Tech\n"
            "🔬 Technical interests: ML, data science, AI engineering, web/mobile/backend "
            "development"
        ),
    },
    {
        "slug": "andrii-bilan",
        "name": "Andrii Bilan",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Ukraine",
        "sort_order": 40,
        "skills": "Programming, AI, computer technology",
        "portrait": "images/team/andrii-bilan.webp",
        "bio": (
            "🇺🇦 Country: Ukraine\n"
            "🏫 School: Lyceum No. 19 “Mezhyhirskyi”\n"
            "🎓 Grade: 9th grade\n"
            "💻 Focus: Programming, AI, computer technology\n"
            "🤖 IOAI 2026: Honourable Mention\n"
            "📊 IOAI 2026 rank: 248th\n"
            "🥉 Infomatrix 2026: Bronze Medal\n"
            "🧑‍💻 Codeforces: Andrii_Bilan\n"
            "🧑‍💻 E-Olymp: andriy_bilan"
        ),
    },
    {
        "slug": "chanitha-sendinu-denagama",
        "name": "Chanitha Sendinu Denagama",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Sri Lanka",
        "sort_order": 50,
        "skills": "AI, ML, software development, robotics & IoT",
        "portrait": "images/team/chanitha-sendinu-denagama.webp",
        "bio": (
            "🇱🇰 Country: Sri Lanka\n"
            "🏫 School: Sivali Central College, Ratnapura\n"
            "🤖 Focus: AI, ML, software development, robotics & IoT\n"
            "🧠 IOAI 2026: Honourable Mention\n"
            "🌎 IOAI 2026: Sri Lanka national-team member\n"
            "💻 NOI 2026: National finalist\n"
            "🚀 Projects: HealStream, C-Effect, Aeolian Nexus\n"
            "🏆 Earlier activities: Robotics, invention competitions, aviation, sports"
        ),
    },
    {
        "slug": "albert-rodrigo-alvarez-jove",
        "name": "Albert Rodrigo Alvarez Jove",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Peru",
        "sort_order": 60,
        "skills": "Mathematics, Artificial Intelligence, Machine Learning, "
        "Computational competitions",
        "portrait": "images/team/albert-rodrigo-alvarez-jove.webp",
        "bio": (
            "Field: Mathematics • Artificial Intelligence • Machine Learning • "
            "Computational competitions\n"
            "Country: Peru 🇵🇪\n"
            "School: Saco Oliveros, Lima\n"
            "Notable achievements:\n"
            "- 🥇 1st, 2022 Torneo de Jóvenes Matemáticos — national 1st-secondary "
            "category\n"
            "- 🥈 2nd, OPEIA 2026 — Peru's AI Olympiad\n"
            "- 🥉 2025 Iranian Geometry Olympiad — Advanced category\n"
            "- 🇵🇪 Peru representative at IOAI 2026\n"
            "- 🏅 IOAI 2026 Honourable Mention"
        ),
    },
    {
        "slug": "aboubacar-bangoura",
        "name": "Aboubacar Bangoura",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Guinea",
        "sort_order": 70,
        "skills": "Artificial Intelligence",
        "portrait": "images/team/aboubacar-bangoura.webp",
        "bio": (
            "🇬🇳 Country: Guinea\n"
            "🤖 Field: Artificial Intelligence\n"
            "🌍 International representation: Guinea at IOAI 2026\n"
            "🏆 Competition: International Olympiad in Artificial Intelligence 2026"
        ),
    },
    {
        "slug": "prince-kumar-mandal",
        "name": "Prince Kumar Mandal",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Nepal",
        "sort_order": 80,
        "skills": "Artificial Intelligence, Machine Learning, Neural Networks, "
        "Image Segmentation",
        "portrait": "images/team/prince-kumar-mandal.webp",
        "bio": (
            "🇳🇵 Country: Nepal\n"
            "🏫 Institution: St. Xavier’s College, Kathmandu\n"
            "🤖 Focus: Artificial Intelligence & Machine Learning\n"
            "🧠 Interests: Neural Networks, Classification, KNN, Image Segmentation\n"
            "🌏 International representation: Nepal at IOAI 2025\n"
            "💻 Field: Computer Science / AI research"
        ),
    },
    {
        "slug": "peter-r-kandel",
        "name": "Peter R. Kandel",
        "role": "Co-Founder",
        "group": "cofounder",
        "country": "Nepal",
        "sort_order": 90,
        "skills": "Artificial Intelligence, Software Engineering, Mathematics",
        "portrait": "images/team/peter-r-kandel.webp",
        "github_url": "https://github.com/peterkandel",
        "bio": (
            "🇳🇵 Based in: Kathmandu, Nepal\n"
            "🤖 Focus: Artificial Intelligence, Software Engineering, Mathematics\n"
            "🏆 Olympiads: National top 20 in Math and AI\n"
            "💻 Projects: NATERIDA—award-winning robotics team project; independently "
            "built flood victim tracking app\n"
            "📚 Research: Collaborating with a PhD professor at Tribhuvan University\n"
            "🧠 Interests: Computer Vision, Robotics, Accessible Technology"
        ),
    },
    # ------------------------------------------------------------ national heads
    {
        "slug": "ayan-zeeshan-national-head",
        "name": "Ayan Zeeshan",
        "role": "Pakistan National Head",
        "group": "national_head",
        "country": "Pakistan",
        "sort_order": 10,
        "skills": "Artificial Intelligence",
        "portrait": "images/team/ayan-zeeshan.webp",
        "bio": "Scientiae et Patriae.",
    },
    {
        "slug": "huzaifa-gulzar-shaikh",
        "name": "Huzaifa Gulzar Shaikh",
        "role": "National Head",
        "group": "national_head",
        "country": "India",
        "sort_order": 20,
        "skills": "Programming, AI/ML, Python",
        "portrait": "images/team/huzaifa-gulzar-shaikh.webp",
        "bio": (
            "Country: India\n"
            "📍 Location: Sharjah (UAE past), Maharashtra (India current)\n"
            "💻 Focus: Programming, AI/ML, Python\n"
            "🧠 Started coding: Around age 9\n"
            "🤖 AI project: FIFA Data Exploration & Insights Generation\n"
            "👁️ Computer vision: YOLOv11-based real-time posture recognition\n"
            "🎓 School: VIBGYOR HIGH School"
        ),
    },
    {
        "slug": "peter-r-kandel-national-head",
        "name": "Peter R. Kandel",
        "role": "National Head",
        "group": "national_head",
        "country": "Nepal",
        "sort_order": 30,
        "skills": "Artificial Intelligence, Software Engineering, Mathematics",
        "portrait": "images/team/peter-r-kandel.webp",
        "github_url": "https://github.com/peterkandel",
        "bio": (
            "🇳🇵 Based in: Kathmandu, Nepal\n"
            "🤖 Focus: Artificial Intelligence, Software Engineering, Mathematics\n"
            "🏆 Olympiads: National top 20 in Math and AI\n"
            "💻 Projects: NATERIDA—award-winning robotics team project; independently "
            "built flood victim tracking app\n"
            "📚 Research: Collaborating with a PhD professor at Tribhuvan University\n"
            "🧠 Interests: Computer Vision, Robotics, Accessible Technology"
        ),
    },
    {
        "slug": "serena-li",
        "name": "Serena Li",
        "role": "National Head",
        "group": "national_head",
        "country": "Australia",
        "sort_order": 40,
        "skills": "AI, Natural Sciences, Machine Learning",
        "portrait": "images/team/serena-li.webp",
        "bio": (
            "🇦🇺 SERENA LI | AI & SCIENCE\n\n"
            "🏆 APOAI 2026 Honourable Mention\n"
            "🤖 AIO Gold Medalist 🥇\n"
            "💻 Informatics Olympiad Participant\n"
            "💻 IOAI Participant 2026\n"
            "🧬 Interests: Natural Sciences & Machine Learning\n"
            "🔬 Camps: Biology & JSO\n\n"
            "🌏 Representing Australia at the Asia-Pacific Olympiad in Artificial "
            "Intelligence (APOAI) 2026."
        ),
    },
]


# ------------------------------------------------------------------- projects
PROJECT_RECORDS: list[dict] = [
    {
        "slug": "naterida",
        "title": "NATERIDA",
        "category": "Robotics",
        "featured": True,
        "sort_order": 10,
        "contributors": "Peter R. Kandel",
        "summary": "Award-winning robotics team project from Kathmandu, Nepal.",
        "description": (
            "**NATERIDA** is an award-winning robotics team project listed among the work "
            "of ADHAYAN co-founder Peter R. Kandel, based in Kathmandu, Nepal.\n\n"
            "Peter's stated technical interests are computer vision, robotics and "
            "accessible technology."
        ),
        "meta_description": "NATERIDA — an award-winning robotics team project by ADHAYAN "
        "co-founder Peter R. Kandel.",
    },
    {
        "slug": "flood-victim-tracking-app",
        "title": "Flood victim tracking app",
        "category": "Software",
        "sort_order": 20,
        "contributors": "Peter R. Kandel",
        "summary": "An independently built application for tracking flood victims.",
        "description": (
            "A flood victim tracking application built independently by ADHAYAN "
            "co-founder Peter R. Kandel.\n\n"
            "The project sits alongside his research collaboration with a PhD professor "
            "at Tribhuvan University."
        ),
    },
    {
        "slug": "transformer-from-scratch",
        "title": "Transformer from scratch",
        "category": "AI & ML",
        "featured": True,
        "sort_order": 30,
        "contributors": "Pitambar Lamichhane",
        "tech_stack": "Python, Deep Learning",
        "summary": "A from-scratch implementation of the Transformer architecture.",
        "description": (
            "A Transformer implemented from scratch, part of the algorithmic and "
            "computational project work of ADHAYAN co-founder Pitambar Lamichhane.\n\n"
            "Stated interests behind the work: neural networks, optimization and "
            "AI research."
        ),
    },
    {
        "slug": "adhayan-weekly-competition-2",
        "title": "ADHAYAN Weekly Competition 2 — Teach Dmytro to read",
        "category": "Competition",
        "featured": True,
        "sort_order": 40,
        "contributors": "Andrii Bilan",
        "tech_stack": "Kaggle, Machine Learning",
        "demo_url": "https://www.kaggle.com/competitions/adhayan-weekly-competition-2",
        "summary": "Weekly competition #2, hosted on Kaggle and created by Andrii Bilan.",
        "description": (
            "ADHAYAN Weekly competition #2 🎉🏆\n\n"
            "**Task:** Teach Dmytro to read\n\n"
            "The task was made by Andrii Bilan, the national head of Ukraine 🇺🇦, who can "
            "be contacted at bilan.a@academy.com.ua if anything misfunctions.\n\n"
            "The competition is hosted on Kaggle. Good luck! 🍀🚀"
        ),
        "meta_description": "ADHAYAN Weekly Competition 2 — Teach Dmytro to read, hosted "
        "on Kaggle.",
    },
    {
        "slug": "fifa-data-exploration",
        "title": "FIFA Data Exploration & Insights Generation",
        "category": "Data Science",
        "sort_order": 50,
        "contributors": "Huzaifa Gulzar Shaikh",
        "summary": "An AI/data project exploring FIFA data and generating insights.",
        "description": (
            "FIFA Data Exploration & Insights Generation — the AI project listed by "
            "ADHAYAN national head Huzaifa Gulzar Shaikh (India), who works on "
            "programming, AI/ML and Python."
        ),
    },
    {
        "slug": "yolov11-posture-recognition",
        "title": "Real-time posture recognition with YOLOv11",
        "category": "Computer Vision",
        "sort_order": 60,
        "contributors": "Huzaifa Gulzar Shaikh",
        "tech_stack": "YOLOv11, Computer Vision",
        "summary": "A YOLOv11-based real-time posture recognition system.",
        "description": (
            "A YOLOv11-based real-time posture recognition system listed among the "
            "computer-vision work of ADHAYAN national head Huzaifa Gulzar Shaikh."
        ),
    },
    {
        "slug": "healstream-c-effect-aeolian-nexus",
        "title": "HealStream, C-Effect & Aeolian Nexus",
        "category": "Software",
        "sort_order": 70,
        "contributors": "Chanitha Sendinu Denagama",
        "summary": "Three projects built by ADHAYAN co-founder Chanitha Sendinu Denagama.",
        "description": (
            "**HealStream**, **C-Effect** and **Aeolian Nexus** are the projects listed by "
            "ADHAYAN co-founder Chanitha Sendinu Denagama (Sri Lanka), whose focus areas "
            "are AI, ML, software development, robotics and IoT."
        ),
    },
]


# --------------------------------------------------------------------- blog posts
BLOG_RECORDS: list[dict] = [
    {
        "slug": "introducing-adhayan",
        "title": "Introducing ADHAYAN",
        "author": "ADHAYAN Founding Team",
        "category": "Organization",
        "tags": "introduction, community, mission",
        "featured": True,
        "published_at": datetime(2026, 10, 1, 0, 0),
        "excerpt": (
            "ADHAYAN is a youth-driven academic network built to connect curious minds, "
            "expand access to meaningful learning, and turn ideas into action."
        ),
        "meta_description": "Introducing ADHAYAN — Learn. Connect. Create.",
        "content": (
            "# Learn. Connect. Create.\n\n"
            "ADHAYAN — **AI-Driven Hub for Advanced Youth and Academic Networking** — is "
            "an international research and collaboration initiative focused on artificial "
            "intelligence and related fields.\n\n"
            "ADHAYAN is a youth-driven academic network built to connect curious minds, "
            "expand access to meaningful learning, and turn ideas into action.\n\n"
            "We bring together students, educators, researchers, and organizations to "
            "learn beyond the classroom through academic communities, competitions, "
            "research, mentorship, and collaboration.\n\n"
            "From discovering a new field to building something of your own, ADHAYAN "
            "creates the space, connections, and opportunities for young people to "
            "explore, create, and grow.\n\n"
            "## What we set out to do\n\n"
            "1. **International research collaboration** — bring together researchers, "
            "students, developers, and innovators working in AI from across the globe.\n"
            "2. **Knowledge sharing** — exchange research findings, methodologies and "
            "insights among the international AI research community.\n"
            "3. **Capacity building** — support emerging researchers and practitioners "
            "through mentorship, collaboration opportunities and shared resources.\n"
            "4. **Global community development** — build a genuinely international "
            "initiative with active participation from multiple countries and regions.\n\n"
            "## Where we are from\n\n"
            "ADHAYAN was established in **Nepal** and connects people across **Sri Lanka, "
            "Pakistan, Bangladesh, Papua New Guinea, Peru, India, Ukraine, Guinea** and "
            "**Australia**.\n"
        ),
    },
    {
        "slug": "founding-declaration-and-timeline",
        "title": "ADHAYAN: Founding Declaration & Timeline",
        "author": "ADHAYAN Founding Team",
        "category": "Organization",
        "tags": "founding, history, declaration",
        "published_at": datetime(2026, 9, 1, 0, 0),
        "excerpt": (
            "ADHAYAN was established in Nepal on September 1, 2026, by the founding team "
            "of Pitambar Lamichhane, Prashanna Tiwari and Prince Kumar Mandal."
        ),
        "meta_description": "The founding declaration and timeline of ADHAYAN, established "
        "in Nepal on September 1, 2026.",
        "content": (
            "# Founding Declaration\n\n"
            "ADHAYAN was established in Nepal on **September 1, 2026**, following the "
            "founding meeting of Pitambar Lamichhane, Prashanna Tiwari, and Prince Kumar "
            "Mandal, who collectively initiated the organization as an international "
            "research and collaboration initiative focused on artificial intelligence and "
            "related fields.\n\n"
            "The founding team subsequently began outreach and collaboration with "
            "individuals and prospective members across Nepal, Sri Lanka, Pakistan, "
            "Bangladesh, Papua New Guinea, Peru, and other countries with the objective "
            "of developing ADHAYAN as a global research community.\n\n"
            "## Timeline\n\n"
            "| Date | Event |\n| --- | --- |\n"
            "| September 1, 2026 | Founding meeting held; ADHAYAN established by decision "
            "of the three founding members (Nepal) |\n"
            "| September 1, 2026 | Organization name “ADHAYAN” adopted and first "
            "used |\n"
            "| September 2026 | Founding team begins international outreach |\n"
            "| September–October 2026 | Initial collaboration with individuals in Sri "
            "Lanka, Pakistan, Bangladesh, Papua New Guinea and Peru |\n"
            "| October 2026 | Official ADHAYAN logo created and first used |\n"
            "| October 2026 | ADHAYAN GitHub repository created for organizational "
            "documentation |\n"
            "| October 2026 | Official ADHAYAN LinkedIn page established |\n\n"
            "## Founding members\n\n"
            "| Name | Role | Country of origin |\n| --- | --- | --- |\n"
            "| Pitambar Lamichhane | Founding Member | Nepal |\n"
            "| Prashanna Tiwari | Founding Member | Nepal |\n"
            "| Prince Kumar Mandal | Founding Member | Nepal |\n\n"
            "## Founding purpose\n\n"
            "1. **International Research Collaboration**\n"
            "2. **Knowledge Sharing**\n"
            "3. **Capacity Building**\n"
            "4. **Global Community Development**\n\n"
            "> This declaration is a dated record of first adoption, use, authorship, and "
            "organizational activity. It is not a legal registration of any kind.\n"
        ),
    },
]


# ---------------------------------------------------------------- announcements
ANNOUNCEMENT_RECORDS: list[dict] = [
    {
        "slug": "weekly-competition-2-teach-dmytro-to-read",
        "title": "Weekly competition 2 | Teach Dmytro to read",
        "category": "Competition Announcement",
        "published_at": datetime(2026, 10, 12, 0, 0),
        "sort_order": 10,
        "featured": True,
        "summary": "ADHAYAN announces weekly competition #2 by Andrii Bilan.",
        "meta_description": "ADHAYAN weekly competition #2 — Teach Dmytro to read.",
        "body": (
            "Hello guys! 👋\n\n"
            "We are glad to announce ADHAYAN Weekly competition #2 🎉🏆\n\n"
            "**Task:** Teach Dmytro to read\n\n"
            "The task was made by Andrii Bilan, the national head of Ukraine 🇺🇦  \n"
            "Email: bilan.a@academy.com.ua 💬\n\n"
            "If anything happens, something misfunctions, feel free to contact him at any "
            "time! 🛠📩\n\n"
            "Most importantly have fun and learn new things! 🤖📚✨\n\n"
            "The competition is hosted on Kaggle:\n\n"
            "🔗 https://www.kaggle.com/competitions/adhayan-weekly-competition-2\n\n"
            "Good luck! 🍀🚀"
        ),
    },
    {
        "slug": "official-channels-launched",
        "title": "Official ADHAYAN channels launched",
        "category": "Update",
        "published_at": datetime(2026, 10, 1, 0, 0),
        "sort_order": 20,
        "summary": (
            "The official logo, GitHub repository and LinkedIn page are now live."
        ),
        "meta_description": "Official ADHAYAN logo, GitHub repository and LinkedIn page "
        "are now live.",
        "body": (
            "October 2026 has been a busy month for ADHAYAN:\n\n"
            "- Official **ADHAYAN logo** created and first used\n"
            "- **ADHAYAN GitHub repository** created for organizational documentation\n"
            "- Official **LinkedIn page** established: "
            "https://www.linkedin.com/company/adhayan/\n\n"
            "You can follow the initiative on LinkedIn for open calls, competitions and "
            "collaboration opportunities."
        ),
    },
    {
        "slug": "adhayan-established-in-nepal",
        "title": "ADHAYAN established in Nepal",
        "category": "Milestone",
        "published_at": datetime(2026, 9, 1, 0, 0),
        "sort_order": 30,
        "summary": (
            "ADHAYAN was established on September 1, 2026 as an international research "
            "and collaboration initiative."
        ),
        "meta_description": "ADHAYAN was established in Nepal on September 1, 2026.",
        "body": (
            "ADHAYAN was established in **Nepal** on **September 1, 2026**, following the "
            "founding meeting of Pitambar Lamichhane, Prashanna Tiwari, and Prince Kumar "
            "Mandal.\n\n"
            "The founding team began international outreach in September 2026, with "
            "initial communications and collaboration in Sri Lanka, Pakistan, Bangladesh, "
            "Papua New Guinea and Peru.\n\n"
            "The name **ADHAYAN** stands for *AI-Driven Hub for Advanced Youth and "
            "Academic Networking*."
        ),
    },
]


# ------------------------------------------------------------------- events
EVENT_RECORDS: list[dict] = [
    {
        "model": "competition",
        "slug": "adhayan-weekly-competition-2",
        "title": "ADHAYAN Weekly Competition 2 — Teach Dmytro to read",
        "category": "Competition",
        "status": "upcoming",
        "mode": "online",
        "location": "Online — Kaggle",
        "starts_at": datetime(2026, 10, 12, 0, 0),
        "registration_url": "https://www.kaggle.com/competitions/adhayan-weekly-competition-2",
        "sort_order": 10,
        "summary": "Weekly competition #2 created by Andrii Bilan, national head of Ukraine.",
        "description": (
            "**Task:** Teach Dmytro to read\n\n"
            "ADHAYAN Weekly competition #2, created by Andrii Bilan — national head of "
            "Ukraine 🇺🇦 (bilan.a@academy.com.ua).\n\n"
            "The competition is hosted on Kaggle. Have fun and learn new things! 🤖📚✨"
        ),
        "meta_description": "ADHAYAN Weekly Competition 2 — Teach Dmytro to read.",
    },
]


# ------------------------------------------------------------------ publications
# The bundled PDF is copied into the uploads folder by ``import_content`` so the
# Zenodo-style record page can preview and serve it.
_PAPER_PDF_REPO_PATH = Path("research") / "guardrailer-paper.pdf"
_PAPER_PDF_UPLOAD_PATH = "papers/guardrailer-paper.pdf"

PUBLICATION_RECORDS: list[dict] = [
    {
        "slug": "lightweight-prompt-injection-detection",
        "title": (
            "Lightweight Prompt Injection Detection: From Centroid-Based Embedding "
            "Classification to a Hybrid Guardrail"
        ),
        "author_name": "Prashanna Tiwari",
        "abstract": (
            "Prompt injection remains one of the most practical threats to large language "
            "model (LLM) applications. This paper presents a lightweight approach to "
            "prompt-injection detection, moving from centroid-based embedding "
            "classification toward a hybrid guardrail. We introduce **Guardrailer v1**, a "
            "dataset of **722,842 prompts**, and show that a simple embedding-centroid "
            "classifier already captures a large share of injections, while a hybrid "
            "guardrail combining complementary signals improves robustness at low "
            "overhead. The method is designed to run close to the model with minimal "
            "latency, making it suitable for production guardrails."
        ),
        "keywords": "prompt injection, LLM security, guardrails, embeddings, classification",
        "doi": "10.5281/zenodo.22124698",
        "license": "CC BY 4.0",
        "pdf_path": _PAPER_PDF_UPLOAD_PATH,
        "pdf_filename": "PAPER.pdf",
        "pdf_size": 1_300_000,
        "github_url": "https://github.com/dev-prashanna/Prompt_Injection_Detection",
        "dataset_url": (
            "https://www.kaggle.com/datasets/prashannadeveloper/guardrailer-dataset-v1"
        ),
        "software_language": "Python",
        "software_status": "Active",
        "references": (
            "Greshake, K. et al. Not what you've signed up for: Compromising Real-World "
            "LLM-Integrated Applications. (2023)\n"
            "Perez, F. & Ribeiro, I. Ignore This Title and HackAPrompt: Exposing "
            "Systemic Weaknesses of LLMs Through a Global Prompt Injection Competition. "
            "(2023)\n"
            "Schneider, J. et al. Prompt Injection Attacks and Defenses in LLM-Integrated "
            "Applications. (2023)"
        ),
        "status": "published",
        "featured": True,
        "published_at": datetime(2026, 8, 27, 0, 0),
        "meta_description": (
            "A lightweight approach to prompt-injection detection, from centroid-based "
            "embedding classification to a hybrid guardrail."
        ),
    },
]


# --------------------------------------------------------------------- datasets
DATASET_RECORDS: list[dict] = [
    {
        "slug": "guardrailer-dataset-v1",
        "title": "Guardrailer v1 — Prompt Injection Dataset",
        "source": "Kaggle",
        "source_url": (
            "https://www.kaggle.com/datasets/prashannadeveloper/guardrailer-dataset-v1"
        ),
        "license": "CC BY 4.0",
        "size_label": "208 MB · 722,842 prompts",
        "tags": "prompt injection, LLM security, guardrails, dataset",
        "sort_order": 10,
        "summary": (
            "A large-scale prompt-injection dataset backing the Lightweight Prompt "
            "Injection Detection paper."
        ),
        "description": (
            "**Guardrailer v1** is a large-scale prompt-injection dataset used to train and "
            "evaluate lightweight injection detectors. It contains **722,842 prompts** "
            "(~208 MB) and is released under **CC BY 4.0**.\n\n"
            "The dataset accompanies the paper *Lightweight Prompt Injection Detection: "
            "From Centroid-Based Embedding Classification to a Hybrid Guardrail*."
        ),
        "meta_description": (
            "Guardrailer v1 — a 722k-prompt injection dataset on Kaggle (CC BY 4.0)."
        ),
    },
]


# --------------------------------------------------------------------- helpers
def apply_default_settings(db, force: bool = False) -> int:
    """Create any missing site settings. Existing values are kept unless forced."""
    created = 0
    for order, (key, value, label, group, field_type) in enumerate(DEFAULT_SETTINGS):
        row = SiteSetting.query.filter_by(key=key).first()
        if row is None:
            row = SiteSetting(
                key=key,
                value=value,
                label=label,
                group=group,
                field_type=field_type,
                sort_order=order,
            )
            db.session.add(row)
            created += 1
        else:
            row.label = row.label or label
            row.group = row.group or group
            row.field_type = row.field_type or field_type
            row.sort_order = order
            if force:
                row.value = value
    db.session.flush()
    return created


def _insert(db, model, record: dict) -> bool:
    """Insert ``record`` when its slug is new. Returns True when inserted."""
    slug = record["slug"]
    if model.query.filter_by(slug=slug).first() is not None:
        return False
    row = model(**{k: v for k, v in record.items() if k != "model"})
    db.session.add(row)
    db.session.flush()
    return True


def import_content(db) -> dict[str, int]:
    """Import original content and GitHub pins. Safe to run repeatedly."""
    counts = {
        "settings": apply_default_settings(db),
        "team": 0,
        "projects": 0,
        "posts": 0,
        "announcements": 0,
        "events": 0,
        "competitions": 0,
        "publications": 0,
        "datasets": 0,
    }

    for record in TEAM_RECORDS:
        counts["team"] += int(_insert(db, TeamMember, record))
    # Upgrade only the unchanged original NATERIDA seed, preserving CMS edits.
    legacy = PROJECT_RECORDS[0]
    naterida = Project.query.filter_by(slug="naterida").first()
    if naterida is not None and all(
        getattr(naterida, key) == value for key, value in legacy.items()
    ) and not any((naterida.github_url, naterida.demo_url, naterida.cover_image,
                   naterida.tech_stack)) and naterida.status == "published":
        replacement = next(r for r in PINNED_PROJECT_RECORDS if r["slug"] == "naterida")
        for key, value in replacement.items():
            setattr(naterida, key, value)
        naterida.meta_description = replacement["summary"]
    for record in PINNED_PROJECT_RECORDS:
        # Bundle source images in the repository and serve copies through the
        # existing media route, including installations with cached templates.
        cover = record.get("cover_image", "")
        if cover:
            source = Path(current_app.static_folder) / cover
            destination = Path(current_app.config["UPLOAD_FOLDER"]) / cover
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copyfile(source, destination)
        counts["projects"] += int(_insert(db, Project, record))
        project = Project.query.filter_by(slug=record["slug"]).one()
        # Backfill repository covers for pins imported before images were added.
        if (
            not project.cover_image
            or project.cover_image == "/static/images/projects/project-jerry.jpeg"
            or project.cover_image == "/static/" + cover
        ) and project.github_url == record["github_url"]:
            project.cover_image = cover
    for record in PROJECT_RECORDS:
        counts["projects"] += int(_insert(db, Project, record))
    # Correct the original segmentation credit while preserving custom CMS edits.
    segmentation = Project.query.filter_by(slug="image-segmentation-naterida").first()
    if segmentation is not None and segmentation.contributors == (
        "Prasiddha Mainali, Prashanna Tiwari, Prince Kumar Mandal"
    ):
        segmentation.contributors = "Prashanna Tiwari"
    from app.project_covers import backfill_project_covers

    backfill_project_covers(Project)
    for record in BLOG_RECORDS:
        counts["posts"] += int(_insert(db, BlogPost, record))
    for record in ANNOUNCEMENT_RECORDS:
        counts["announcements"] += int(_insert(db, Announcement, record))
    for record in EVENT_RECORDS:
        model = Competition if record["model"] == "competition" else Event
        counts["competitions" if record["model"] == "competition" else "events"] += int(
            _insert(db, model, record)
        )
    for record in DATASET_RECORDS:
        counts["datasets"] += int(_insert(db, Dataset, record))
    for record in PUBLICATION_RECORDS:
        counts["publications"] += int(_insert(db, Publication, record))
    from app.repository_publications import import_repository_publications

    counts["publications"] += import_repository_publications(db)

    # Publish the bundled paper PDF so the record page can preview and serve it.
    publication = Publication.query.filter_by(
        slug="lightweight-prompt-injection-detection"
    ).first()
    if publication is not None and publication.pdf_path:
        destination = Path(current_app.config["UPLOAD_FOLDER"]) / publication.pdf_path
        source = Path(current_app.static_folder) / _PAPER_PDF_REPO_PATH
        if source.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copyfile(source, destination)

    db.session.commit()
    return counts
