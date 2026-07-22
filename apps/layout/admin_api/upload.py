"""Admin API — page image/video upload for visual builder."""

from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.blog.admin_api.logging_utils import log_upload_failure, log_upload_unexpected_error
from apps.blog.admin_api.responses import permission_denied
from apps.page.media import EditorMediaError, EditorMediaService
from apps.layout.admin_api.permissions import can_edit_cms_page
from apps.layout.models import CMSPage


def _user_id(request) -> int | None:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return user.pk
    return None


@require_POST
def page_upload_image_view(request, page_id: int):
    page = get_object_or_404(CMSPage, pk=page_id, page_type=CMSPage.PageType.PROJEKTI)

    if not can_edit_cms_page(request, page):
        return permission_denied()

    upload = request.FILES.get("image")
    if upload is None:
        log_upload_failure(post_id=page.pk, user_id=_user_id(request), code="missing_image")
        return JsonResponse({"ok": False, "error": "missing_image"}, status=400)

    service = EditorMediaService(media_scope="projects")
    try:
        result = service.upload_image(upload, request=request)
    except EditorMediaError as exc:
        log_upload_failure(post_id=page.pk, user_id=_user_id(request), code=exc.code)
        return JsonResponse({"ok": False, "error": exc.code}, status=400)
    except Exception as exc:
        log_upload_unexpected_error(post_id=page.pk, user_id=_user_id(request), exc=exc)
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
def page_upload_video_view(request, page_id: int):
    page = get_object_or_404(CMSPage, pk=page_id, page_type=CMSPage.PageType.PROJEKTI)

    if not can_edit_cms_page(request, page):
        return permission_denied()

    upload = request.FILES.get("video")
    if upload is None:
        log_upload_failure(post_id=page.pk, user_id=_user_id(request), code="missing_video")
        return JsonResponse({"ok": False, "error": "missing_video"}, status=400)

    service = EditorMediaService(media_scope="projects")
    try:
        result = service.upload_video(upload, request=request)
    except EditorMediaError as exc:
        log_upload_failure(post_id=page.pk, user_id=_user_id(request), code=exc.code)
        return JsonResponse({"ok": False, "error": exc.code}, status=400)
    except Exception as exc:
        log_upload_unexpected_error(post_id=page.pk, user_id=_user_id(request), exc=exc)
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
