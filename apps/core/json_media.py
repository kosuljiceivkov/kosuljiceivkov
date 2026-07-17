"""Reference tracking and conservative cleanup for page-builder media."""
from __future__ import annotations

from dataclasses import dataclass

from django.apps import apps
from django.core.files.storage import storages
from django.db import transaction
from django.db.models import FileField

MANAGED_PREFIXES: dict[str, tuple[str, ...]] = {
    "blog_images": (
        "page/document/",
        "page/featured/",
        "seo/og/",
        "seo/twitter/",
        "builder/",
    ),
    "project_videos": (
        "page/videos/",
        "builder/videos/",
    ),
}


@dataclass(frozen=True)
class JsonMediaRef:
    storage: str
    path: str


def _is_managed_ref(ref: JsonMediaRef) -> bool:
    prefixes = MANAGED_PREFIXES.get(ref.storage, ())
    return any(ref.path.startswith(prefix) for prefix in prefixes)


def _storage_alias_for_storage(storage) -> str:
    for alias in MANAGED_PREFIXES:
        try:
            if storages[alias] is storage:
                return alias
        except Exception:
            continue
    location = getattr(storage, "location", None)
    if location is not None:
        for alias in MANAGED_PREFIXES:
            try:
                if getattr(storages[alias], "location", None) == location:
                    return alias
            except Exception:
                continue
    return "blog_images"


def extract_media_refs_from_page(page) -> set[JsonMediaRef]:
    refs: set[JsonMediaRef] = set()
    if not isinstance(page, dict):
        return refs

    for section in page.get("sections") or []:
        for row in section.get("rows") or []:
            for column in row.get("columns") or []:
                for block in column.get("blocks") or []:
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get("type")
                    if block_type not in {"image", "video"}:
                        continue
                    attrs = block.get("attrs") or {}
                    if not isinstance(attrs, dict):
                        continue

                    path = str(attrs.get("path") or "").strip()
                    if block_type == "image":
                        if path:
                            refs.add(JsonMediaRef("blog_images", path))
                        continue

                    if path:
                        refs.add(JsonMediaRef("project_videos", path))
                    poster_path = str(attrs.get("poster_path") or "").strip()
                    poster_src = str(
                        attrs.get("poster") or attrs.get("poster_src") or ""
                    ).strip()
                    if poster_path:
                        refs.add(JsonMediaRef("blog_images", poster_path))
                    elif poster_src and not poster_src.startswith(
                        ("http://", "https://", "/")
                    ):
                        refs.add(JsonMediaRef("blog_images", poster_src))

    return refs


def all_page_media_refs() -> set[JsonMediaRef]:
    from apps.blog.models import BlogPost
    from apps.layout.models import CMSPage

    refs: set[JsonMediaRef] = set()
    for model in (BlogPost, CMSPage):
        for page in model.objects.values_list("body_page", flat=True):
            refs.update(extract_media_refs_from_page(page))
    return refs


def all_file_media_refs() -> set[JsonMediaRef]:
    refs: set[JsonMediaRef] = set()
    for model in apps.get_models():
        file_fields = [
            field for field in model._meta.fields if isinstance(field, FileField)
        ]
        if not file_fields:
            continue
        for values in model._default_manager.values_list(
            *(field.attname for field in file_fields)
        ):
            if not isinstance(values, tuple):
                values = (values,)
            for field, value in zip(file_fields, values):
                path = str(value or "").strip()
                if not path:
                    continue
                refs.add(
                    JsonMediaRef(
                        _storage_alias_for_storage(field.storage),
                        path,
                    )
                )
    return refs


def all_media_refs() -> set[JsonMediaRef]:
    return all_page_media_refs() | all_file_media_refs()


def _delete_ref(ref: JsonMediaRef) -> None:
    if not _is_managed_ref(ref):
        return
    try:
        storages[ref.storage].delete(ref.path)
    except Exception:
        pass


def cleanup_removed_json_media(old_refs, new_refs) -> int:
    """Delete only removed builder files that no saved page still references."""
    removed = set(old_refs) - set(new_refs)
    if not removed:
        return 0

    deleted = 0
    for ref in removed:
        if not _is_managed_ref(ref):
            continue

        def _delete(target_ref=ref):
            if target_ref in all_media_refs():
                return
            try:
                storages[target_ref.storage].delete(target_ref.path)
            except Exception:
                pass

        transaction.on_commit(_delete)
        deleted += 1
    return deleted


def cleanup_deleted_page_media(instance) -> int:
    """Delete page media from a removed object unless another page still uses it."""
    refs = extract_media_refs_from_page(getattr(instance, "body_page", None))
    if not refs:
        return 0

    def cleanup():
        referenced = all_media_refs()
        for ref in refs - referenced:
            _delete_ref(ref)

    transaction.on_commit(cleanup)
    return len(refs)


def parse_pending_media_items(raw_items) -> list[dict[str, str]]:
    if not isinstance(raw_items, list):
        return []

    items: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        storage = str(item.get("storage") or "blog_images").strip() or "blog_images"
        path = str(item.get("path") or "").strip()
        if not path:
            continue
        key = (storage, path)
        if key in seen:
            continue
        seen.add(key)
        items.append({"storage": storage, "path": path})
    return items


def cleanup_pending_paths(items) -> int:
    referenced = all_media_refs()
    deleted = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        storage = str(item.get("storage") or "blog_images").strip() or "blog_images"
        path = str(item.get("path") or "").strip()
        if not path:
            continue
        ref = JsonMediaRef(storage, path)
        if _is_managed_ref(ref) and ref not in referenced:
            _delete_ref(ref)
            deleted += 1
    return deleted
