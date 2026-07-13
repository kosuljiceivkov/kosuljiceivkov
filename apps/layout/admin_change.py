"""Pomoćne funkcije za ProjektiPage admin change form."""

from __future__ import annotations

import json
from typing import Any

from django.urls import reverse

from apps.layout.admin_preview_links import get_admin_preview_url
from apps.layout.models import CMSPage
from apps.page.catalog.elements import build_builder_catalog
from apps.page.normalize import normalize_page
from apps.page.schema import empty_page
from apps.seo.services import get_seo_metadata


def build_projekti_change_form_context(request, page: CMSPage) -> dict[str, Any]:
    """Kontekst za custom change form šablon."""
    metadata = get_seo_metadata(page)
    initial_page = normalize_page(page.body_page) if page.body_page else empty_page()

    return {
        "blog_editor_mode": "visual",
        "blog_preview_url": get_admin_preview_url(page),
        "blog_page_save_url": reverse(
            "admin:layout_projektipage_page_save",
            args=[page.pk],
        ),
        "blog_catalog_url": reverse("admin:blog_blogpost_page_builder_catalog"),
        "blog_upload_url": reverse(
            "admin:layout_projektipage_page_upload_image",
            args=[page.pk],
        ),
        "blog_video_upload_url": reverse(
            "admin:layout_projektipage_page_upload_video",
            args=[page.pk],
        ),
        "blog_cleanup_pending_url": reverse(
            "admin:layout_projektipage_page_cleanup_pending_media",
            args=[page.pk],
        ),
        "blog_initial_page": initial_page,
        "blog_initial_page_json": json.dumps(initial_page, ensure_ascii=False),
        "blog_page_version": page.page_version,
        "blog_seo_score": metadata.seo_score if metadata else None,
        "blog_focus_title": not page.has_page_content(),
        "blog_changelist_url": reverse("admin:index"),
        "blog_draft_title_placeholder": "",
        "blog_draft_slug_prefix": "",
        "blog_builder_catalog": build_builder_catalog(),
    }
