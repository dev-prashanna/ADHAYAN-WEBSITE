"""Markdown rendering that is safe to embed in public pages."""

from __future__ import annotations

import nh3

ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "dl", "dt", "dd",
    "blockquote", "pre", "code", "em", "strong", "del", "ins", "sub", "sup",
    "a", "img", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    "span", "div", "figure", "figcaption", "abbr", "kbd", "mark", "input",
}

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "loading", "width", "height"],
    "code": ["class"],
    "pre": ["class"],
    "span": ["class"],
    "div": ["class"],
    "td": ["align", "colspan", "rowspan"],
    "th": ["align", "colspan", "rowspan", "scope"],
    "ol": ["start"],
    "input": ["type", "checked", "disabled"],
    "h1": ["id"],
    "h2": ["id"],
    "h3": ["id"],
    "h4": ["id"],
    "h5": ["id"],
    "h6": ["id"],
}

ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}

# NH3 requires a mapping of tag -> set(attributes).
_ATTRIBUTES = {tag: set(attrs) for tag, attrs in ALLOWED_ATTRIBUTES.items()}

_MARKDOWN_EXTENSIONS = [
    "extra",           # tables, fenced code, footnotes, attr_list
    "sane_lists",
    "smarty",
    "toc",
    "codehilite",
]

_EXTENSION_CONFIG = {
    "codehilite": {
        "guess_lang": False,
        "noclasses": False,
        "pygments_style": "monokai",
        "use_pygments": True,
    },
    "toc": {"permalink": False},
}


def render_markdown(text: str | None) -> str:
    """Convert Markdown to sanitized HTML.

    The output of the ``markdown`` library is run through NH3 (Ammonia) so
    untrusted input can never inject script tags or event handlers.
    """
    if not text:
        return ""

    import markdown as md

    html = md.markdown(
        text,
        extensions=_MARKDOWN_EXTENSIONS,
        extension_configs=_EXTENSION_CONFIG,
        output_format="html5",
    )
    return sanitize_html(html)


def sanitize_html(html: str) -> str:
    """Allow-list sanitiser used for Markdown output *and* admin-entered HTML."""
    if not html:
        return ""
    cleaned = nh3.clean(
        html,
        tags=set(ALLOWED_TAGS),
        attributes=_ATTRIBUTES,
        url_schemes=set(ALLOWED_URL_SCHEMES),
        link_rel="noopener noreferrer",
        strip_comments=True,
    )
    return cleaned
