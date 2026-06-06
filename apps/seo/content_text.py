"""Izvlačenje običnog teksta iz sadržaja za SEO fallback i čitljivost."""

from __future__ import annotations

import re

from apps.layout.builder_models import Block
from apps.layout.builder_services import get_sections_for_object

_WHITESPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip())


def split_sentences(text: str) -> list[str]:
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return []
    parts = _SENTENCE_SPLIT_RE.split(cleaned)
    return [part.strip() for part in parts if part.strip()]


def _text_from_block(block: Block) -> str:
    chunks: list[str] = []

    if block.block_type == Block.BlockType.TEXT and block.text_content:
        chunks.append(block.text_content)

    if block.block_type == Block.BlockType.HEADING and block.heading_text:
        chunks.append(block.heading_text)

    if block.block_type == Block.BlockType.BUTTON and block.button_label:
        chunks.append(block.button_label)

    if block.block_type == Block.BlockType.CAROUSEL:
        carousel = getattr(block, "carousel", None)
        if carousel is not None:
            for item in carousel.items.all():
                if item.title:
                    chunks.append(item.title)
                if item.description:
                    chunks.append(item.description)

    return " ".join(chunks)


def get_builder_plain_text(page_object, *, visible_only=True, max_length=600) -> str:
    """Prvi tekstualni sadržaj iz page buildera, skraćen za meta opis."""
    if page_object is None or not getattr(page_object, "pk", None):
        return ""

    sections = get_sections_for_object(page_object, visible_only=visible_only)
    chunks: list[str] = []
    total = 0

    for section in sections:
        for row in section.rows.all():
            for column in row.columns.all():
                for block in column.blocks.all():
                    block_text = normalize_whitespace(_text_from_block(block))
                    if not block_text:
                        continue
                    chunks.append(block_text)
                    total += len(block_text)
                    if total >= max_length:
                        return normalize_whitespace(" ".join(chunks))[:max_length]

    return normalize_whitespace(" ".join(chunks))[:max_length]


def get_content_plain_text(page_object, *, visible_only=True, max_length=600) -> str:
    """Kombinuje uvod/excerpt i builder tekst za SEO i čitljivost."""
    parts: list[str] = []

    excerpt = getattr(page_object, "excerpt", "")
    if excerpt and excerpt.strip():
        parts.append(excerpt.strip())

    builder_text = get_builder_plain_text(
        page_object,
        visible_only=visible_only,
        max_length=max_length,
    )
    if builder_text:
        parts.append(builder_text)

    combined = normalize_whitespace(" ".join(parts))
    return combined[:max_length]
