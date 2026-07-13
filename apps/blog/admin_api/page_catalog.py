"""Admin API — builder catalog."""

from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.page.catalog.elements import build_builder_catalog


@require_GET
def page_builder_catalog_view(request):
    return JsonResponse({"ok": True, "catalog": build_builder_catalog()})
