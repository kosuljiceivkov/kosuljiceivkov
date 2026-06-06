"""Izvlačenje slika iz sadržaja za SEO analizu."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from apps.layout.builder_models import Block
from apps.seo.content_analysis import _iter_blocks
from apps.seo.helpers import get_image_dimensions

_FILENAME_STEM = re.compile(r"^(.+?)(?:\.[a-z0-9]{2,5})?$", re.I)


@dataclass(frozen=True)
class PageImageEntry:
    source: str
    label: str
    alt_text: str
    filename: str
    basename: str
    width: int | None
    height: int | None
    file_size: int
    format_name: str

    @property
    def has_alt(self) -> bool:
        return bool(self.alt_text.strip())

    @property
    def stem(self) -> str:
        match = _FILENAME_STEM.match(self.basename)
        return (match.group(1) if match else self.basename).lower()


def _text_has_alt(value: str) -> bool:
    return bool((value or "").strip())


def page_has_missing_alt(page_object, *, visible_only: bool = False) -> bool:
    """Brza provera alt teksta bez otvaranja fajlova slika."""
    if page_object is None or not getattr(page_object, "pk", None):
        return False

    featured = getattr(page_object, "featured_image", None)
    if featured and getattr(featured, "name", ""):
        title_alt = getattr(page_object, "title", "") or ""
        if not _text_has_alt(title_alt):
            return True

    for block in _iter_blocks(page_object, visible_only=visible_only):
        if block.block_type == Block.BlockType.IMAGE and block.image:
            if getattr(block.image, "name", "") and not _text_has_alt(
                block.image_alt or block.image_caption
            ):
                return True

        if block.block_type == Block.BlockType.GALLERY:
            for gallery_image in block.gallery_images.all():
                if gallery_image.image and getattr(gallery_image.image, "name", ""):
                    if not _text_has_alt(gallery_image.alt_text or gallery_image.caption):
                        return True

        if block.block_type == Block.BlockType.CAROUSEL:
            carousel = getattr(block, "carousel", None)
            if carousel is not None:
                for item in carousel.items.all():
                    if item.image and getattr(item.image, "name", ""):
                        if not _text_has_alt(item.alt_text or item.title):
                            return True

    return False


def _inspect_image_field(image_field) -> tuple[int | None, int | None, int, str]:
    if not image_field or not getattr(image_field, "name", ""):
        return None, None, 0, ""

    width, height = get_image_dimensions(image_field)
    file_size = 0
    format_name = ""

    try:
        file_size = int(image_field.size or 0)
    except Exception:
        file_size = 0

    if width and height:
        return width, height, file_size, format_name

    try:
        image_field.open("rb")
        with Image.open(image_field) as image:
            width, height = image.size
            format_name = (image.format or "").upper()
    except (UnidentifiedImageError, OSError, ValueError):
        pass
    finally:
        if hasattr(image_field, "close"):
            try:
                image_field.close()
            except Exception:
                pass

    return width, height, file_size, format_name


def _entry_from_field(
    *,
    image_field,
    source: str,
    label: str,
    alt_text: str = "",
) -> PageImageEntry | None:
    if not image_field or not getattr(image_field, "name", ""):
        return None

    filename = image_field.name
    basename = os.path.basename(filename)
    width, height, file_size, format_name = _inspect_image_field(image_field)

    return PageImageEntry(
        source=source,
        label=label,
        alt_text=alt_text,
        filename=filename,
        basename=basename,
        width=width,
        height=height,
        file_size=file_size,
        format_name=format_name,
    )


def collect_page_images(page_object, *, visible_only: bool = False) -> list[PageImageEntry]:
    if page_object is None or not getattr(page_object, "pk", None):
        return []

    images: list[PageImageEntry] = []

    featured = getattr(page_object, "featured_image", None)
    featured_entry = _entry_from_field(
        image_field=featured,
        source="featured",
        label="Istaknuta slika",
        alt_text=getattr(page_object, "title", "") or "",
    )
    if featured_entry is not None:
        images.append(featured_entry)

    for block in _iter_blocks(page_object, visible_only=visible_only):
        if block.block_type == Block.BlockType.IMAGE and block.image:
            entry = _entry_from_field(
                image_field=block.image,
                source="builder_image",
                label=f"Slika (blok #{block.pk})",
                alt_text=block.image_alt or block.image_caption or "",
            )
            if entry is not None:
                images.append(entry)

        if block.block_type == Block.BlockType.GALLERY:
            for index, gallery_image in enumerate(block.gallery_images.all(), start=1):
                entry = _entry_from_field(
                    image_field=gallery_image.image,
                    source="gallery",
                    label=f"Galerija #{block.pk} · slika {index}",
                    alt_text=gallery_image.alt_text or gallery_image.caption or "",
                )
                if entry is not None:
                    images.append(entry)

        if block.block_type == Block.BlockType.CAROUSEL:
            carousel = getattr(block, "carousel", None)
            if carousel is not None:
                for index, item in enumerate(carousel.items.all(), start=1):
                    entry = _entry_from_field(
                        image_field=item.image,
                        source="carousel",
                        label=f"Karusel #{block.pk} · slajd {index}",
                        alt_text=item.alt_text or item.title or "",
                    )
                    if entry is not None:
                        images.append(entry)

    return images
