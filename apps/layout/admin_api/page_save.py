"""Admin API — manual page save for Projekti visual builder."""

from __future__ import annotations

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.blog.admin_api.logging_utils import (
    log_page_save_invalid_json,
    log_page_save_unexpected_error,
    log_page_save_validation_error,
    log_page_save_version_conflict,
)
from apps.blog.admin_api.responses import parse_json_body, permission_denied, word_count
from apps.layout.admin_api.permissions import can_edit_cms_page
from apps.layout.models import CMSPage
from apps.page.update import PageVersionConflictError, apply_body_page_update
from apps.page.validation import PageValidationError


def _user_id(request) -> int | None:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return user.pk
    return None


@require_POST
def page_save_view(request, page_id: int):
    page = get_object_or_404(CMSPage, pk=page_id, page_type=CMSPage.PageType.PROJEKTI)

    if not can_edit_cms_page(request, page):
        return permission_denied()

    payload = parse_json_body(request)
    if payload is None:
        log_page_save_invalid_json(post_id=page.pk, user_id=_user_id(request))
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    body_page = payload.get("body_page")
    if not isinstance(body_page, dict):
        log_page_save_invalid_json(post_id=page.pk, user_id=_user_id(request))
        return JsonResponse({"ok": False, "error": "missing_body_page"}, status=400)

    expected_version = payload.get("expected_page_version")
    if expected_version is not None:
        try:
            expected_version = int(expected_version)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "invalid_expected_version"}, status=400)

    try:
        with transaction.atomic():
            locked_page = CMSPage.objects.select_for_update().get(pk=page.pk)
            result = apply_body_page_update(
                locked_page,
                body_page,
                expected_version=expected_version,
            )

            update_fields = ["updated_at"]
            if result.changed:
                update_fields.extend(
                    [
                        "body_page",
                        "body_plaintext",
                        "body_format",
                        "page_version",
                    ]
                )
                locked_page.save(update_fields=update_fields)
            else:
                locked_page.save(update_fields=update_fields)

    except PageVersionConflictError as exc:
        log_page_save_version_conflict(
            post_id=page.pk,
            user_id=_user_id(request),
            expected=exc.expected,
            actual=exc.actual,
        )
        return JsonResponse(
            {
                "ok": False,
                "error": "version_conflict",
                "page_version": exc.actual,
                "expected_page_version": exc.expected,
                "message": "Stranica je izmenjena u drugoj sesiji. Osvežite stranicu.",
            },
            status=409,
        )
    except PageValidationError as exc:
        log_page_save_validation_error(
            post_id=page.pk,
            user_id=_user_id(request),
            messages=exc.errors,
        )
        return JsonResponse(
            {
                "ok": False,
                "error": "validation_error",
                "messages": exc.errors,
            },
            status=400,
        )
    except Exception as exc:
        log_page_save_unexpected_error(post_id=page.pk, user_id=_user_id(request), exc=exc)
        return JsonResponse(
            {
                "ok": False,
                "error": "server_error",
                "message": "Neočekivana greška pri čuvanju stranice.",
            },
            status=500,
        )

    locked_page.refresh_from_db(fields=["updated_at", "body_plaintext", "page_version"])

    return JsonResponse(
        {
            "ok": True,
            "changed": result.changed,
            "page_version": locked_page.page_version,
            "saved_at": locked_page.updated_at.isoformat(),
            "word_count": word_count(locked_page.body_plaintext),
        }
    )
