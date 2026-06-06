"""Strukturirani sadržaj za analizu čitljivosti."""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.layout.builder_models import Block
from apps.seo.content_analysis import _iter_blocks, _paragraph_text, _heading_text
from apps.seo.content_text import get_content_plain_text, normalize_whitespace, split_sentences


@dataclass(frozen=True)
class HeadingEntry:
    level: str
    text: str


@dataclass(frozen=True)
class ReadabilityContentInput:
    content: str = ""
    sentences: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    headings: list[HeadingEntry] = field(default_factory=list)
    word_count: int = 0


def _split_paragraphs(text: str) -> list[str]:
    if not text:
        return []

    parts = re_split_paragraphs(text)
    return [normalize_whitespace(part) for part in parts if normalize_whitespace(part)]


def re_split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    chunks = normalized.split("\n\n")
    if len(chunks) <= 1 and "\n" in normalized:
        chunks = normalized.split("\n")
    return chunks


def extract_readability_content(page_object, *, visible_only=False) -> ReadabilityContentInput:
    paragraphs: list[str] = []
    headings: list[HeadingEntry] = []
    content_chunks: list[str] = []

    excerpt = getattr(page_object, "excerpt", "") if page_object else ""
    if excerpt and excerpt.strip():
        paragraphs.extend(_split_paragraphs(excerpt.strip()))
        content_chunks.append(excerpt.strip())

    for block in _iter_blocks(page_object, visible_only=visible_only):
        heading = _heading_text(block)
        if heading:
            headings.append(
                HeadingEntry(
                    level=block.heading_level or Block.HeadingLevel.H2,
                    text=heading,
                )
            )
            content_chunks.append(heading)

        paragraph = _paragraph_text(block)
        if paragraph:
            paragraphs.extend(_split_paragraphs(paragraph) or [paragraph])
            content_chunks.append(paragraph)

    if page_object is not None and getattr(page_object, "pk", None):
        full_text = get_content_plain_text(page_object, visible_only=visible_only, max_length=20000)
    else:
        full_text = normalize_whitespace(" ".join(content_chunks))

    if not paragraphs and full_text:
        paragraphs = split_sentences(full_text) or [full_text]

    sentences = split_sentences(full_text)
    word_count = len(full_text.split()) if full_text else 0

    return ReadabilityContentInput(
        content=full_text.strip(),
        sentences=sentences,
        paragraphs=paragraphs,
        headings=headings,
        word_count=word_count,
    )


def build_readability_content_input(
    content_object,
    *,
    overrides: dict | None = None,
    visible_only: bool = False,
) -> ReadabilityContentInput:
    overrides = overrides or {}
    base = extract_readability_content(content_object, visible_only=visible_only)

    excerpt = overrides.get("excerpt", "").strip()
    if excerpt:
        paragraphs = _split_paragraphs(excerpt)
        if paragraphs:
            content = normalize_whitespace(excerpt)
            if base.content and excerpt not in base.content:
                content = normalize_whitespace(f"{excerpt} {base.content}")
            return ReadabilityContentInput(
                content=content,
                sentences=split_sentences(content),
                paragraphs=paragraphs + base.paragraphs,
                headings=base.headings,
                word_count=len(content.split()),
            )

    return base
