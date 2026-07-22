"""Admin API — page image/video upload."""

from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.blog.admin_api.logging_utils import (
    log_upload_failure,
    log_upload_unexpected_error,
)
from apps.blog.admin_api.permissions import can_edit_blog_post
from apps.blog.admin_api.responses import permission_denied
from apps.blog.models import BlogPost
from apps.page.media import EditorMediaError, EditorMediaService


def _user_id(request) -> int | None:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return user.pk
    return None


@require_POST
def page_upload_image_view(request, post_id: int):
    post = get_object_or_404(BlogPost, pk=post_id)

    if not can_edit_blog_post(request, post):
        return permission_denied()

    upload = request.FILES.get("image")
    if upload is None:
        log_upload_failure(post_id=post.pk, user_id=_user_id(request), code="missing_image")
        return JsonResponse({"ok": False, "error": "missing_image"}, status=400)

    service = EditorMediaService(media_scope="blog")
    try:
        result = service.upload_image(upload, request=request)
    except EditorMediaError as exc:
        log_upload_failure(post_id=post.pk, user_id=_user_id(request), code=exc.code)
        return JsonResponse({"ok": False, "error": exc.code}, status=400)
    except Exception as exc:
        log_upload_unexpected_error(post_id=post.pk, user_id=_user_id(request), exc=exc)
        return JsonResponse(
            {
                "ok": False,
                "error": "server_error",
                "message": "Neočekivana greška pri otpremanju slike.",
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "url": result.url,
            "path": result.path,
            "storage": result.storage,
            "alt": result.alt,
        }
    )


@require_POST
def page_upload_video_view(request, post_id: int):
    post = get_object_or_404(BlogPost, pk=post_id)

    if not can_edit_blog_post(request, post):
        return permission_denied()

    upload = request.FILES.get("video")
    if upload is None:
        log_upload_failure(post_id=post.pk, user_id=_user_id(request), code="missing_video")
        return JsonResponse({"ok": False, "error": "missing_video"}, status=400)

    service = EditorMediaService(media_scope="blog")
    try:
        result = service.upload_video(upload, request=request)
    except EditorMediaError as exc:
        log_upload_failure(post_id=post.pk, user_id=_user_id(request), code=exc.code)
        return JsonResponse({"ok": False, "error": exc.code}, status=400)
    except Exception as exc:
        log_upload_unexpected_error(post_id=post.pk, user_id=_user_id(request), exc=exc)
        return JsonResponse(
            {
                "ok": False,
                "error": "server_error",
                "message": "Neočekivana greška pri otpremanju videa.",
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "url": result.url,
            "path": result.path,
            "storage": result.storage,
        }
    )
