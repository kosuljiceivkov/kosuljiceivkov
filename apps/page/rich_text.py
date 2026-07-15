"""Inline HTML sanitization for text blocks."""

from __future__ import annotations

import re
from html import escape, unescape
from html.parser import HTMLParser

ALLOWED_INLINE_TAGS = frozenset({"b", "strong", "i", "em", "u", "br", "span"})
FONT_SIZE_MIN_PX = 8
FONT_SIZE_MAX_PX = 96
_FONT_SIZE_RE = re.compile(r"font-size:\s*([0-9]+(?:\.[0-9]+)?)px", re.IGNORECASE)


def normalize_html_entities(value: str) -> str:
    """Dekodira višestruko escape-ovane entitete i pretvara NBSP u običan razmak."""
    normalized = value or ""
    for _ in range(8):
        decoded = unescape(normalized)
        if decoded == normalized:
            break
        normalized = decoded
    return normalized.replace("\xa0", " ")


def normalize_font_size_px(style: str) -> str | None:
    match = _FONT_SIZE_RE.search(style or "")
    if not match:
        return None
    try:
        value = round(float(match.group(1)))
    except (TypeError, ValueError):
        return None
    if value < FONT_SIZE_MIN_PX or value > FONT_SIZE_MAX_PX:
        return None
    return f"{value}px"


class _InlineHTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag_name = tag.lower()
        if tag_name == "span":
            font_size = normalize_font_size_px(dict(attrs).get("style", ""))
            if font_size:
                self._parts.append(f'<span style="font-size: {font_size}">')
                self._open_tags.append("span")
            return
        if tag_name in ALLOWED_INLINE_TAGS:
            self._parts.append(f"<{tag_name}>")
            if tag_name != "br":
                self._open_tags.append(tag_name)

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name == "br":
            return
        if self._open_tags and self._open_tags[-1] == tag_name:
            self._parts.append(f"</{tag_name}>")
            self._open_tags.pop()

    def handle_data(self, data: str) -> None:
        self._parts.append(escape(normalize_html_entities(data)))

    def get_html(self) -> str:
        while self._open_tags:
            tag_name = self._open_tags.pop()
            self._parts.append(f"</{tag_name}>")
        return "".join(self._parts).strip()


def sanitize_inline_html(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if "<" not in raw:
        return escape(normalize_html_entities(raw))
    parser = _InlineHTMLSanitizer()
    parser.feed(raw)
    parser.close()
    return parser.get_html()


def inline_html_to_plaintext(value: str) -> str:
    from django.utils.html import strip_tags

    return normalize_html_entities(strip_tags(value or "")).strip()
