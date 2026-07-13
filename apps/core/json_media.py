"""
Izvlačenje i čišćenje medijskih putanja iz page JSON sadržaja (iv_page_v1).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse

from django.core.files.storage import storages

from apps.core.media_cleanup_service import cleanup_media_file, schedule_media_cleanup
from apps.core.media_registry import media_identity, normalize_media_name, storage_key

logger = logging.getLogger("apps.core.json_media")

BLOG_IMAGE_PATH_PREFIXES = (
    "blog/document/",
    "blog/featured/",
    "builder/",
    "seo/",
    "page/posters/",
)
VIDEO_PATH_PREFIXES = (
    "page/videos/",
    "builder/videos/",
)
_VIDEO_EXTENSIONS = frozenset({".mp4", ".webm", ".mov", ".m4v", ".ogv"})


@dataclass(frozen=True, slots=True)
class JsonMediaRef:
    storage_alias: str
    path: str

    @property
    def identity(self) -> tuple[str, str] | None:
        try:
            storage = storages[self.storage_alias]
        except Exception:
            return None
        return media_identity(self.path, storage)


def _storage_base_url(alias: str) -> str:
    storage = storages[alias]
    base_url = getattr(storage, "base_url", "") or ""
    if base_url and not base_url.endswith("/"):
        base_url = f"{base_url}/"
    return base_url


def path_from_media_value(value: str, *, storage_alias: str | None = None) -> str:
    """Normalizuje putanju iz JSON path polja ili javnog src/url."""
    raw = (value or "").strip()
    if not raw:
        return ""

    if raw.startswith(("http://", "https://", "/media/", "/")):
        for alias in ("blog_images", "project_videos"):
            base_url = _storage_base_url(alias)
            if base_url and raw.startswith(base_url):
                return normalize_media_name(raw[len(base_url) :])

        if raw.startswith("/media/"):
            trimmed = raw[len("/media/") :]
            for alias in ("blog_images", "project_videos"):
                location = getattr(storages[alias], "location", "") or ""
                location_name = str(location).replace("\\", "/").strip("/")
                if location_name and trimmed.startswith(f"{location_name}/"):
                    return normalize_media_name(trimmed[len(location_name) + 1 :])
            return normalize_media_name(trimmed)

        parsed = urlparse(raw)
        return normalize_media_name(parsed.path.lstrip("/"))

    return normalize_media_name(raw)


def resolve_json_media_ref(
    value: str,
    *,
    storage_alias: str | None = None,
) -> JsonMediaRef | None:
    path = path_from_media_value(value, storage_alias=storage_alias)
    if not path:
        return None

    alias = storage_alias or _guess_storage_alias(path)
    return JsonMediaRef(storage_alias=alias, path=path)


def _guess_storage_alias(path: str) -> str:
    lowered = path.lower()
    if any(lowered.startswith(prefix) for prefix in VIDEO_PATH_PREFIXES):
        return "project_videos"
    if any(lowered.endswith(ext) for ext in _VIDEO_EXTENSIONS):
        return "project_videos"
    return "blog_images"


def _add_ref(refs: set[JsonMediaRef], value: str, *, storage_alias: str | None = None) -> None:
    ref = resolve_json_media_ref(value, storage_alias=storage_alias)
    if ref is not None:
        refs.add(ref)


def extract_media_refs_from_page(page: Any) -> set[JsonMediaRef]:
    refs: set[JsonMediaRef] = set()
    if not isinstance(page, dict):
        return refs

    for section in page.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for row in section.get("rows") or []:
            if not isinstance(row, dict):
                continue
            for column in row.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                for block in column.get("blocks") or []:
                    _collect_page_block_media(block, refs)
    return refs


def _collect_page_block_media(block: Any, refs: set[JsonMediaRef]) -> None:
    if not isinstance(block, dict):
        return

    block_type = block.get("type")
    attrs = block.get("attrs") or {}
    if not isinstance(attrs, dict):
        return

    if block_type == "image":
        path = str(attrs.get("path") or "").strip()
        src = str(attrs.get("src") or "").strip()
        if path:
            _add_ref(refs, path, storage_alias="blog_images")
        elif src:
            _add_ref(refs, src, storage_alias="blog_images")
        return

    if block_type == "video":
        path = str(attrs.get("path") or "").strip()
        src = str(attrs.get("src") or "").strip()
        poster_path = str(attrs.get("poster_path") or "").strip()
        poster_src = str(attrs.get("poster_src") or "").strip()
        if path:
            _add_ref(refs, path, storage_alias="project_videos")
        elif src:
            _add_ref(refs, src, storage_alias="project_videos")
        if poster_path:
            _add_ref(refs, poster_path, storage_alias="blog_images")
        elif poster_src:
            _add_ref(refs, poster_src, storage_alias="blog_images")


def extract_media_refs_from_host(instance) -> set[JsonMediaRef]:
    refs: set[JsonMediaRef] = set()

    body_page = getattr(instance, "body_page", None)
    if body_page:
        refs |= extract_media_refs_from_page(body_page)

    return refs


def collect_json_media_identities() -> set[tuple[str, str]]:
    from apps.blog.models import BlogPost
    from apps.layout.models import CMSPage

    identities: set[tuple[str, str]] = set()

    for obj in BlogPost.objects.iterator(chunk_size=200):
        for ref in extract_media_refs_from_host(obj):
            identity = ref.identity
            if identity:
                identities.add(identity)

    for obj in CMSPage.objects.iterator(chunk_size=200):
        for ref in extract_media_refs_from_host(obj):
            identity = ref.identity
            if identity:
                identities.add(identity)

    return identities


def cleanup_json_media_refs(
    refs: Iterable[JsonMediaRef],
    *,
    reason: str,
) -> None:
    for ref in refs:
        try:
            storage = storages[ref.storage_alias]
        except Exception:
            logger.exception(
                "Unknown storage alias for JSON media cleanup",
                extra={"storage_alias": ref.storage_alias, "path": ref.path},
            )
            continue
        cleanup_media_file(ref.path, storage, reason=reason)


def cleanup_removed_json_media(
    old_refs: set[JsonMediaRef],
    new_refs: set[JsonMediaRef],
    *,
    reason: str = "json_content_replaced",
) -> None:
    removed = {ref for ref in old_refs if ref not in new_refs}
    if not removed:
        return

    def _run():
        cleanup_json_media_refs(removed, reason=reason)

    schedule_media_cleanup(_run)


def cleanup_host_json_media(instance, *, reason: str = "host_deleted") -> None:
    refs = extract_media_refs_from_host(instance)
    if not refs:
        return

    def _run():
        cleanup_json_media_refs(refs, reason=reason)

    schedule_media_cleanup(_run)


def json_media_identity_set(refs: set[JsonMediaRef]) -> set[tuple[str, str]]:
    identities: set[tuple[str, str]] = set()
    for ref in refs:
        identity = ref.identity
        if identity:
            identities.add(identity)
    return identities
