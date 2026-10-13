"""Markdown rendering and XSS sanitisation."""

from __future__ import annotations

from app.utils.markdown import render_markdown, sanitize_html


def test_empty_input():
    assert render_markdown(None) == ""
    assert render_markdown("") == ""
    assert sanitize_html("") == ""


def test_basic_markdown():
    html = render_markdown("# Title\n\nSome **bold** text.")
    assert "<h1" in html
    assert "<strong>bold</strong>" in html


def test_code_block_highlighted():
    html = render_markdown("```python\nprint('hi')\n```")
    assert "<pre" in html
    assert "highlight" in html or "codehilite" in html or "<code" in html


def test_table_rendered():
    html = render_markdown("| a | b |\n| --- | --- |\n| 1 | 2 |")
    assert "<table" in html
    assert "<td" in html


def test_script_tags_stripped():
    html = render_markdown('<script>alert("xss")</script>\n\nhello')
    assert "<script" not in html
    assert "alert" not in html or "&lt;" in html
    assert "hello" in html


def test_event_handler_stripped():
    cleaned = sanitize_html('<img src="x" onerror="alert(1)">')
    assert "onerror" not in cleaned


def test_javascript_url_blocked():
    cleaned = sanitize_html('<a href="javascript:alert(1)">click</a>')
    assert "javascript:" not in cleaned


def test_safe_links_kept():
    cleaned = sanitize_html('<a href="https://example.com">ok</a>')
    assert "https://example.com" in cleaned
    assert "noopener" in cleaned


def test_iframe_stripped():
    cleaned = sanitize_html('<iframe src="https://evil.example"></iframe>')
    assert "<iframe" not in cleaned
