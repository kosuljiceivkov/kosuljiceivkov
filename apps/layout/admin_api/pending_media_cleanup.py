"""Admin API — briše privremene upload-e ako editor napusti Projekti bez čuvanja."""

from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.blog.admin_api.responses import parse_json_body, permission_denied
from apps.core.json_media import cleanup_pending_paths, parse_pending_media_items
from apps.layout.admin_api.permissions import can_edit_cms_page
from apps.layout.models import CMSPage


@require_POST
def page_cleanup_pending_media_view(request, page_id: int):
    page = get_object_or_404(CMSPage, pk=page_id, page_type=CMSPage.PageType.PROJEKTI)

    if not can_edit_cms_page(request, page):
        return permission_denied()

    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    deleted = cleanup_pending_paths(parse_pending_media_items(payload.get("paths")))

    return JsonResponse({"ok": True, "deleted": deleted})
