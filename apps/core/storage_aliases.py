"""
Rešava Django 5.2 FileField storage alias stringove u STORAGES backend instance.
"""
from __future__ import annotations

import logging

from django.apps import apps
from django.core.files.storage import Storage, storages
from django.db import models

logger = logging.getLogger("apps.core.storage_aliases")

_resolved = False


def resolve_filefield_storage_aliases() -> None:
    """
    Modeli koriste storage="blog_images" string alias.
    Django 5.2 ne rešava alias automatski — mapiramo na storages[alias] pri startu.
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
                try:
                    backend = storages[alias]
                except Exception:
                    logger.exception(
                        "Unknown media storage alias on FileField",
                        extra={
                            "model": model._meta.label,
                            "field": field.name,
                            "alias": alias,
                        },
                    )
                    continue
                field.storage = backend
                field._storage_callable = lambda _alias=alias: storages[_alias]
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
