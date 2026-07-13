"""Pomoćne funkcije za BlogPost admin change form."""

from __future__ import annotations

import json
import uuid
from typing import Any

from django.urls import reverse

from django.utils.text import slugify

from apps.page.catalog.elements import build_builder_catalog
from apps.page.normalize import normalize_page
from apps.page.schema import empty_page
from apps.blog.models import BlogPost
from apps.layout.admin_preview_links import get_admin_preview_url
from apps.seo.services import get_seo_metadata

DRAFT_TITLE_PLACEHOLDER = "Bez naslova"
DRAFT_SLUG_PREFIX = "nacrt-"


def create_visual_builder_draft() -> BlogPost:
    """Kreira prazan nacrt za visual builder — odmah ima pk za upload i čuvanje sadržaja."""
    slug = f"{DRAFT_SLUG_PREFIX}{uuid.uuid4().hex[:12]}"
    return BlogPost.objects.create(
        title=DRAFT_TITLE_PLACEHOLDER,
        slug=slug,
        is_published=False,
    )


def is_placeholder_draft(post: BlogPost) -> bool:
    return post.title == DRAFT_TITLE_PLACEHOLDER and post.slug.startswith(DRAFT_SLUG_PREFIX)


def unique_slug_for_title(title: str, *, exclude_pk: int | None = None) -> str:
    base = slugify(title)[:240] or "clanak"
    candidate = base
    suffix = 2
    while True:
        queryset = BlogPost.objects.filter(slug=candidate)
        if exclude_pk is not None:
            queryset = queryset.exclude(pk=exclude_pk)
        if not queryset.exists():
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def maybe_update_slug_from_title(post: BlogPost) -> None:
    """Ažurira privremeni nacrt slug kada editor unese pravi naslov."""
    if not post.title or post.title == DRAFT_TITLE_PLACEHOLDER:
        return
    if post.slug.startswith(DRAFT_SLUG_PREFIX) or not post.slug:
        post.slug = unique_slug_for_title(post.title, exclude_pk=post.pk)


def build_blog_change_form_context(request, post: BlogPost) -> dict[str, Any]:
    """Kontekst za custom change form šablon."""
    metadata = get_seo_metadata(post)
    initial_page = normalize_page(post.body_page) if post.body_page else empty_page()

    return {
        "blog_preview_url": get_admin_preview_url(post),
        "blog_page_save_url": reverse(
            "admin:blog_blogpost_page_save",
            args=[post.pk],
        ),
        "blog_catalog_url": reverse("admin:blog_blogpost_page_builder_catalog"),
        "blog_upload_url": reverse(
            "admin:blog_blogpost_page_upload_image",
            args=[post.pk],
        ),
        "blog_video_upload_url": reverse(
            "admin:blog_blogpost_page_upload_video",
            args=[post.pk],
        ),
        "blog_cleanup_pending_url": reverse(
            "admin:blog_blogpost_page_cleanup_pending_media",
            args=[post.pk],
        ),
        "blog_initial_page": initial_page,
        "blog_initial_page_json": json.dumps(initial_page, ensure_ascii=False),
        "blog_page_version": post.page_version,
        "blog_seo_score": metadata.seo_score if metadata else None,
        "blog_focus_title": is_placeholder_draft(post) or not post.has_page_content(),
        "blog_changelist_url": reverse("admin:blog_blogpost_changelist"),
        "blog_draft_title_placeholder": DRAFT_TITLE_PLACEHOLDER,
        "blog_draft_slug_prefix": DRAFT_SLUG_PREFIX,
        "blog_builder_catalog": build_builder_catalog(),
    }
