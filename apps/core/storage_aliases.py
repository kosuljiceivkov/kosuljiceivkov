"""
Rešava Django 5.2 FileField storage alias stringove u STORAGES backend instance.

Koristite blog_images_storage / project_videos_storage u modelima — serializabilno
za migracije (za razliku od storage="blog_images" stringa ili lambda).
"""
from __future__ import annotations

import logging

from django.apps import apps
from django.core.files.storage import Storage, storages
from django.db import models

logger = logging.getLogger("apps.core.storage_aliases")

_resolved = False


def blog_images_storage():
    return storages["blog_images"]


def project_videos_storage():
    return storages["project_videos"]


STORAGE_ALIAS_CALLABLES: dict[str, callable] = {
    "blog_images": blog_images_storage,
    "project_videos": project_videos_storage,
    "default": blog_images_storage,
}


def resolve_filefield_storage_aliases() -> None:
    """
    Runtime fallback: string alias → STORAGES backend.
    Modeli bi trebalo da koriste STORAGE_ALIAS_CALLABLES direktno.
    """
    global _resolved
    if _resolved:
        return
    _resolved = True

    resolved_count = 0
    for model in apps.get_models():
        if model._meta.abstract or model._meta.proxy:
            continue
        for field in model._meta.fields:
            if not isinstance(field, models.FileField):
                continue
            if isinstance(field.storage, str):
                alias = field.storage
                storage_callable = STORAGE_ALIAS_CALLABLES.get(alias)
                if storage_callable is None:
                    logger.exception(
                        "Unknown media storage alias on FileField",
                        extra={
                            "model": model._meta.label,
                            "field": field.name,
                            "alias": alias,
                        },
                    )
                    continue
                field._storage_callable = storage_callable
                field.storage = storage_callable()
                resolved_count += 1
            elif not isinstance(field.storage, Storage):
                logger.warning(
                    "Unexpected FileField storage type",
                    extra={
                        "model": model._meta.label,
                        "field": field.name,
                        "storage_type": type(field.storage).__name__,
                    },
                )

    if resolved_count:
        logger.debug("Resolved %s FileField storage alias(es)", resolved_count)


def storage_for_alias(alias: str) -> Storage:
    """Vrati storage backend za alias (npr. blog_images)."""
    return storages[alias]
