"""Čišćenje privremenih editor uploada koje korisnik nije sačuvao u body_page."""

from __future__ import annotations

from typing import Any, Iterable

from django.core.files.storage import storages

from apps.core.json_media import JsonMediaRef, resolve_json_media_ref
from apps.core.media_cleanup_service import CleanupStats, cleanup_media_file

ALLOWED_PENDING_STORAGE_ALIASES = frozenset({"blog_images", "project_videos"})


def parse_pending_media_items(raw_items: Any) -> list[JsonMediaRef]:
    if not isinstance(raw_items, list):
        return []

    refs: list[JsonMediaRef] = []
    seen: set[tuple[str, str]] = set()

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        storage_alias = str(item.get("storage") or "").strip()
        path = str(item.get("path") or "").strip()
        if not path:
            continue

        if storage_alias not in ALLOWED_PENDING_STORAGE_ALIASES:
            ref = resolve_json_media_ref(path)
            if ref is None:
                continue
            storage_alias = ref.storage_alias
            path = ref.path
        else:
            ref = JsonMediaRef(storage_alias=storage_alias, path=path)
            path = ref.path

        key = (storage_alias, path)
        if key in seen:
            continue
        seen.add(key)
        refs.append(JsonMediaRef(storage_alias=storage_alias, path=path))

    return refs


def cleanup_pending_editor_media(
    items: Iterable[JsonMediaRef],
    *,
    reason: str = "pending_editor_abandoned",
) -> CleanupStats:
    stats = CleanupStats()

    for ref in items:
        try:
            storage = storages[ref.storage_alias]
        except Exception:
            stats.errors += 1
            continue

        result = cleanup_media_file(ref.path, storage, reason=reason)
        if result.status in ("deleted", "dry_run"):
            stats.deleted += 1
        elif result.status == "skipped_referenced":
            stats.skipped_referenced += 1
        elif result.status == "missing":
            stats.missing += 1
        elif result.status == "error":
            stats.errors += 1

    return stats
