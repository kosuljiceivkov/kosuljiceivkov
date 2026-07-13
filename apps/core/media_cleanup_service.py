"""
Servis za bezbedno brisanje medijskih fajlova (R2 / lokalno) preko Django storage API-ja.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

from django.core.files.storage import storages
from django.db import models, transaction

from .media_registry import (
    InstanceMediaFile,
    get_media_field_refs,
    get_media_storage_aliases,
    iter_instance_media_files,
    media_identity,
    normalize_media_name,
    storage_key,
)

logger = logging.getLogger("apps.core.media_cleanup")

_OLD_FILES_ATTR = "_media_cleanup_previous_files"


@dataclass
class CleanupStats:
    deleted: int = 0
    skipped_referenced: int = 0
    missing: int = 0
    errors: int = 0
    scanned_storage: int = 0
    referenced_in_db: int = 0
    orphaned: int = 0

    def merge(self, other: CleanupStats) -> None:
        for attr in self.__dataclass_fields__:
            setattr(self, attr, getattr(self, attr) + getattr(other, attr))


@dataclass(frozen=True, slots=True)
class CleanupResult:
    status: str
    name: str
    storage_key: str
    reason: str = ""


def capture_previous_media_files(instance: models.Model) -> None:
    """Poziva se iz pre_save — pamti trenutne vrednosti fajlova iz baze."""
    if not instance.pk:
        setattr(instance, _OLD_FILES_ATTR, ())
        return

    try:
        previous = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        setattr(instance, _OLD_FILES_ATTR, ())
        return

    setattr(instance, _OLD_FILES_ATTR, tuple(iter_instance_media_files(previous)))


def schedule_media_cleanup(func) -> None:
    transaction.on_commit(func)


def count_references(
    name: str,
    storage: object,
    *,
    exclude_instance: models.Model | None = None,
) -> int:
    identity = media_identity(name, storage)
    if identity is None:
        return 0

    total = 0

    for ref in get_media_field_refs():
        qs = ref.model.objects.exclude(**{ref.field_name: ""})
        if exclude_instance is not None and ref.model is exclude_instance.__class__:
            qs = qs.exclude(pk=exclude_instance.pk)

        for obj in qs.iterator(chunk_size=500):
            field_file = getattr(obj, ref.field_name, None)
            if not field_file:
                continue
            obj_name = normalize_media_name(getattr(field_file, "name", "") or "")
            obj_identity = media_identity(obj_name, field_file.storage)
            if obj_identity == identity:
                total += 1

    return total


def is_still_referenced(
    name: str,
    storage: object,
    *,
    exclude_instance: models.Model | None = None,
) -> bool:
    identity = media_identity(name, storage)
    if identity is None:
        return False

    if count_references(name, storage, exclude_instance=exclude_instance) > 0:
        return True

    from apps.core.json_media import collect_json_media_identities

    return identity in collect_json_media_identities()


def delete_storage_file(name: str, storage: object, *, dry_run: bool = False) -> str:
    """
    Briše fajl preko storage API-ja.
    Vraća: deleted | missing | error | dry_run
    """
    normalized = normalize_media_name(name)
    if not normalized:
        return "missing"

    if dry_run:
        return "dry_run"

    try:
        if not storage.exists(normalized):
            return "missing"
        storage.delete(normalized)
        return "deleted"
    except FileNotFoundError:
        return "missing"
    except Exception:
        logger.exception(
            "Media deletion error",
            extra={
                "media_name": normalized,
                "storage_key": storage_key(storage),
            },
        )
        return "error"


def cleanup_media_file(
    name: str,
    storage: object,
    *,
    reason: str,
    exclude_instance: models.Model | None = None,
    dry_run: bool = False,
) -> CleanupResult:
    """Obriši fajl samo ako nema referenci u bazi."""
    normalized = normalize_media_name(name)
    key = storage_key(storage)

    if not normalized:
        return CleanupResult(status="missing", name="", storage_key=key, reason=reason)

    if is_still_referenced(normalized, storage, exclude_instance=exclude_instance):
        logger.info(
            "Media file skipped — still referenced",
            extra={
                "media_name": normalized,
                "storage_key": key,
                "reason": reason,
            },
        )
        return CleanupResult(
            status="skipped_referenced",
            name=normalized,
            storage_key=key,
            reason=reason,
        )

    outcome = delete_storage_file(normalized, storage, dry_run=dry_run)

    if outcome == "deleted":
        logger.info(
            "Media file deleted",
            extra={
                "media_name": normalized,
                "storage_key": key,
                "reason": reason,
            },
        )
    elif outcome == "dry_run":
        logger.info(
            "Media file would be deleted (dry-run)",
            extra={
                "media_name": normalized,
                "storage_key": key,
                "reason": reason,
            },
        )
    elif outcome == "missing":
        logger.info(
            "Media file missing in storage",
            extra={
                "media_name": normalized,
                "storage_key": key,
                "reason": reason,
            },
        )
    else:
        logger.error(
            "Media file deletion failed",
            extra={
                "media_name": normalized,
                "storage_key": key,
                "reason": reason,
            },
        )

    return CleanupResult(status=outcome, name=normalized, storage_key=key, reason=reason)


delete_unused_file = cleanup_media_file


def cleanup_replaced_files(
    old_files: Iterable[InstanceMediaFile],
    new_files: Iterable[InstanceMediaFile],
) -> CleanupStats:
    """Briše fajlove koji više nisu u upotrebi posle zamene."""
    stats = CleanupStats()
    new_identities = {
        media_identity(item.name, item.storage)
        for item in new_files
        if media_identity(item.name, item.storage)
    }

    for old in old_files:
        old_identity = media_identity(old.name, old.storage)
        if old_identity is None or old_identity in new_identities:
            continue
        result = cleanup_media_file(
            old.name,
            old.storage,
            reason="replaced",
        )
        _tally_result(stats, result)

    return stats


def cleanup_instance_files(
    instance: models.Model,
    *,
    reason: str = "instance_deleted",
) -> CleanupStats:
    """Briše sve fajlove instance ako nisu referencirani drugde."""
    stats = CleanupStats()
    for media in iter_instance_media_files(instance):
        result = cleanup_media_file(
            media.name,
            media.storage,
            reason=reason,
        )
        _tally_result(stats, result)
    return stats


def _tally_result(stats: CleanupStats, result: CleanupResult) -> None:
    if result.status in ("deleted", "dry_run"):
        stats.deleted += 1
    elif result.status == "skipped_referenced":
        stats.skipped_referenced += 1
    elif result.status == "missing":
        stats.missing += 1
    elif result.status == "error":
        stats.errors += 1


def collect_db_media_identities() -> set[tuple[str, str]]:
    """Sve (storage_key, name) parove referencirane u bazi."""
    from apps.core.json_media import collect_json_media_identities

    identities: set[tuple[str, str]] = set()
    for ref in get_media_field_refs():
        qs = (
            ref.model.objects.exclude(**{ref.field_name: ""})
            .exclude(**{ref.field_name: None})
            .only("pk", ref.field_name)
        )
        for obj in qs.iterator(chunk_size=500):
            field_file = getattr(obj, ref.field_name, None)
            name = normalize_media_name(getattr(field_file, "name", "") or "")
            if not name:
                continue
            storage = field_file.storage if field_file else ref.field.storage
            identity = media_identity(name, storage)
            if identity:
                identities.add(identity)

    identities |= collect_json_media_identities()
    return identities


def iter_storage_files(storage_alias: str) -> Iterable[tuple[str, object]]:
    """Iterira sve fajlove u datom storage aliasu. Yield: (name, storage)."""
    from django.core.files.storage import FileSystemStorage

    storage = storages[storage_alias]

    if isinstance(storage, FileSystemStorage):
        yield from _iter_filesystem_storage_files(storage)
        return

    if hasattr(storage, "bucket_name") and hasattr(storage, "connection"):
        yield from _iter_s3_storage_files(storage)
        return

    logger.warning(
        "Unsupported storage for orphan scan",
        extra={"storage_alias": storage_alias, "storage_key": storage_key(storage)},
    )


def _iter_filesystem_storage_files(storage) -> Iterable[tuple[str, object]]:
    from pathlib import Path

    root = Path(storage.location)
    if not root.exists():
        return

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel:
            yield rel, storage


def _iter_s3_storage_files(storage) -> Iterable[tuple[str, object]]:
    prefix = storage.location or ""
    if prefix and not prefix.endswith("/"):
        prefix = f"{prefix}/"

    client = storage.connection.meta.client
    paginator = client.get_paginator("list_objects_v2")
    pagination_kwargs = {"Bucket": storage.bucket_name}
    if prefix:
        pagination_kwargs["Prefix"] = prefix

    for page in paginator.paginate(**pagination_kwargs):
        for item in page.get("Contents", []):
            key = item.get("Key", "")
            if not key or key.endswith("/"):
                continue
            name = key[len(prefix) :] if prefix else key
            if name:
                yield name, storage


def cleanup_orphaned_media(
    *,
    dry_run: bool = False,
    storage_aliases: Iterable[str] | None = None,
    batch_size: int = 100,
) -> CleanupStats:
    """
    Skenira R2/lokalna skladišta i briše fajlove koji nisu referencirani u bazi.
    """
    stats = CleanupStats()
    referenced = collect_db_media_identities()
    stats.referenced_in_db = len(referenced)

    aliases = list(storage_aliases) if storage_aliases else list(get_media_storage_aliases())

    for alias in aliases:
        try:
            storage = storages[alias]
        except Exception:
            logger.exception("Cannot load storage alias", extra={"storage_alias": alias})
            stats.errors += 1
            continue

        batch: list[tuple[str, object]] = []

        for name, file_storage in iter_storage_files(alias):
            stats.scanned_storage += 1
            identity = media_identity(name, file_storage)
            if identity and identity in referenced:
                continue

            stats.orphaned += 1
            batch.append((name, file_storage))

            if len(batch) >= batch_size:
                _process_orphan_batch(batch, stats, dry_run=dry_run)
                batch = []

        if batch:
            _process_orphan_batch(batch, stats, dry_run=dry_run)

    return stats


def _process_orphan_batch(
    batch: list[tuple[str, object]],
    stats: CleanupStats,
    *,
    dry_run: bool,
) -> None:
    for name, storage in batch:
        result = cleanup_media_file(
            name,
            storage,
            reason="orphaned",
            dry_run=dry_run,
        )
        _tally_result(stats, result)
