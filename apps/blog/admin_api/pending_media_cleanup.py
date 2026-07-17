"""Admin API — briše privremene upload-e ako editor napusti stranicu bez čuvanja."""

from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.blog.admin_api.permissions import can_edit_blog_post
from apps.blog.admin_api.responses import parse_json_body, permission_denied
from apps.blog.models import BlogPost
from apps.core.json_media import cleanup_pending_paths, parse_pending_media_items


@require_POST
def page_cleanup_pending_media_view(request, post_id: int):
    post = get_object_or_404(BlogPost, pk=post_id)

    if not can_edit_blog_post(request, post):
        return permission_denied()

    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    deleted = cleanup_pending_paths(parse_pending_media_items(payload.get("paths")))

    return JsonResponse({"ok": True, "deleted": deleted})
