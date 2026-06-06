"""Strukturirano izvlačenje sadržaja za SEO analizu ključnih reči."""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.layout.builder_models import Block
from apps.layout.builder_services import get_sections_for_object
from apps.seo.content_text import get_content_plain_text, normalize_whitespace
from apps.seo.services import (
    get_seo_fallback_title,
    get_seo_metadata,
    resolve_meta_description,
    resolve_seo_title,
)


@dataclass(frozen=True)
class ContentAnalysisInput:
    article_title: str = ""
    content: str = ""
    seo_title: str = ""
    meta_description: str = ""
    focus_keyword: str = ""
    h1: str = ""
    first_paragraph: str = ""
    url_slug: str = ""
    image_alt_texts: list[str] = field(default_factory=list)
    image_count: int = 0
    images_with_alt: int = 0
    word_count: int = 0


def _heading_text(block: Block) -> str:
    if block.block_type == Block.BlockType.HEADING and block.heading_text:
        return block.heading_text.strip()
    return ""


def _paragraph_text(block: Block) -> str:
    if block.block_type == Block.BlockType.TEXT and block.text_content:
        return normalize_whitespace(block.text_content)
    return ""


def _alt_texts_from_block(block: Block) -> list[str]:
    alts: list[str] = []

    if block.block_type == Block.BlockType.IMAGE and block.image_alt:
        alts.append(block.image_alt.strip())

    if block.block_type == Block.BlockType.GALLERY:
        for gallery_image in block.gallery_images.all():
            if gallery_image.alt_text:
                alts.append(gallery_image.alt_text.strip())

    if block.block_type == Block.BlockType.CAROUSEL:
        carousel = getattr(block, "carousel", None)
        if carousel is not None:
            for item in carousel.items.all():
                if item.alt_text:
                    alts.append(item.alt_text.strip())

    return alts


def _count_images_in_block(block: Block, image_count: int, images_with_alt: int) -> tuple[int, int]:
    if block.block_type == Block.BlockType.IMAGE and block.image:
        image_count += 1
        if block.image_alt.strip():
            images_with_alt += 1

    if block.block_type == Block.BlockType.GALLERY:
        for gallery_image in block.gallery_images.all():
            if gallery_image.image:
                image_count += 1
                if gallery_image.alt_text.strip():
                    images_with_alt += 1

    if block.block_type == Block.BlockType.CAROUSEL:
        carousel = getattr(block, "carousel", None)
        if carousel is not None:
            for item in carousel.items.all():
                if item.image:
                    image_count += 1
                    if item.alt_text.strip():
                        images_with_alt += 1

    return image_count, images_with_alt


def _iter_blocks(page_object, *, visible_only=True):
    if page_object is None or not getattr(page_object, "pk", None):
        return

    sections = get_sections_for_object(page_object, visible_only=visible_only)
    for section in sections:
        for row in section.rows.all():
            for column in row.columns.all():
                for block in column.blocks.all():
                    yield block


def extract_builder_analysis_parts(page_object, *, visible_only=True) -> dict:
    h1 = ""
    first_heading = ""
    first_paragraph = ""
    content_chunks: list[str] = []
    image_alt_texts: list[str] = []
    image_count = 0
    images_with_alt = 0

    for block in _iter_blocks(page_object, visible_only=visible_only):
        image_alt_texts.extend(_alt_texts_from_block(block))
        image_count, images_with_alt = _count_images_in_block(
            block,
            image_count,
            images_with_alt,
        )

        heading = _heading_text(block)
        if heading:
            content_chunks.append(heading)
            if block.heading_level == Block.HeadingLevel.H1 and not h1:
                h1 = heading
            if not first_heading:
                first_heading = heading

        paragraph = _paragraph_text(block)
        if paragraph:
            content_chunks.append(paragraph)
            if not first_paragraph:
                first_paragraph = paragraph

    if not h1 and first_heading:
        h1 = first_heading

    return {
        "h1": h1,
        "first_paragraph": first_paragraph,
        "content": normalize_whitespace(" ".join(content_chunks)),
        "image_alt_texts": image_alt_texts,
        "image_count": image_count,
        "images_with_alt": images_with_alt,
    }


def build_content_analysis_input(
    content_object,
    metadata=None,
    *,
    overrides: dict | None = None,
    visible_only: bool = False,
) -> ContentAnalysisInput:
    """
    Priprema ulaz za analizu ključnih reči.
    overrides: draft vrednosti iz admin forme (seo_title, focus_keyword, …).
    """
    overrides = overrides or {}
    metadata = metadata if metadata is not None else get_seo_metadata(content_object)

    article_title = overrides.get("article_title") or get_seo_fallback_title(content_object)
    seo_title = overrides.get("seo_title")
    if seo_title is None:
        seo_title = resolve_seo_title(content_object, metadata)

    meta_description = overrides.get("meta_description")
    if meta_description is None:
        meta_description = resolve_meta_description(content_object, metadata)

    focus_keyword = overrides.get("focus_keyword")
    if focus_keyword is None and metadata is not None:
        focus_keyword = metadata.focus_keyword
    focus_keyword = (focus_keyword or "").strip()

    url_slug = overrides.get("url_slug") or getattr(content_object, "slug", "") or ""

    excerpt = overrides.get("excerpt") or getattr(content_object, "excerpt", "") or ""
    builder_parts = extract_builder_analysis_parts(content_object, visible_only=visible_only)

    first_paragraph = overrides.get("first_paragraph") or builder_parts["first_paragraph"]
    if not first_paragraph and excerpt:
        first_paragraph = normalize_whitespace(excerpt)

    h1 = overrides.get("h1") or builder_parts["h1"] or article_title

    content = overrides.get("content")
    if content is None:
        full_text = get_content_plain_text(content_object, visible_only=visible_only, max_length=20000)
        if excerpt and excerpt.strip() and excerpt.strip() not in full_text:
            content = normalize_whitespace(f"{excerpt.strip()} {full_text}")
        else:
            content = full_text or builder_parts["content"]

    image_alt_texts = overrides.get("image_alt_texts")
    if image_alt_texts is None:
        image_alt_texts = builder_parts["image_alt_texts"]

    word_count = len(content.split()) if content else 0

    return ContentAnalysisInput(
        article_title=article_title.strip(),
        content=content.strip(),
        seo_title=seo_title.strip(),
        meta_description=meta_description.strip(),
        focus_keyword=focus_keyword,
        h1=h1.strip(),
        first_paragraph=first_paragraph.strip(),
        url_slug=str(url_slug).strip(),
        image_alt_texts=[alt for alt in image_alt_texts if alt],
        image_count=builder_parts.get("image_count", 0),
        images_with_alt=builder_parts.get("images_with_alt", 0),
        word_count=word_count,
    )
