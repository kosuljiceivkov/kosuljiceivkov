"""Zajednički JSON odgovori za admin API."""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse


def permission_denied() -> JsonResponse:
    return JsonResponse({"ok": False, "error": "permission_denied"}, status=403)


def parse_json_body(request: HttpRequest) -> dict | None:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        return None
    return payload if isinstance(payload, dict) else None


def word_count(plaintext: str) -> int:
    return len(plaintext.split()) if plaintext.strip() else 0
