"""
Brisanje sadržaja vezanog preko GenericForeignKey (builder, SEO) pri brisanju vlasnika.
"""
from __future__ import annotations

import logging
from typing import Iterable

from django.apps import apps
from django.db import models

logger = logging.getLogger("apps.core.generic_cleanup")

GENERIC_OWNED_RELATION_NAMES: tuple[str, ...] = (
    "builder_sections",
    "seo_metadata",
)


def iter_generic_content_owner_models() -> Iterable[type[models.Model]]:
    """Modeli koji imaju builder_sections i/ili seo_metadata GenericRelation."""
    for model in apps.get_models():
        if model._meta.abstract or model._meta.proxy:
            continue
        if any(hasattr(model, name) for name in GENERIC_OWNED_RELATION_NAMES):
            yield model


def cleanup_generic_owned_content(instance: models.Model) -> dict[str, int]:
    """
    Obriši sav builder i SEO sadržaj vezan za instancu pre brisanja vlasnika.

    Section.delete() kaskadno uklanja Row → Column → Block → galeriju/karusel.
    post_delete signali za medije se okidaju za svaki obrisani model.
    """
    deleted_counts: dict[str, int] = {}

    for relation_name in GENERIC_OWNED_RELATION_NAMES:
        relation = getattr(instance, relation_name, None)
        if relation is None:
            continue
        queryset = relation.all()
        count, _details = queryset.delete()
        if count:
            deleted_counts[relation_name] = count
            logger.info(
                "Generic owned content deleted",
                extra={
                    "owner_model": instance.__class__._meta.label,
                    "owner_pk": instance.pk,
                    "relation": relation_name,
                    "deleted_objects": count,
                },
            )

    return deleted_counts


def cleanup_generic_owned_content_before_delete(instance: models.Model) -> None:
    """Poziva se iz pre_delete — GFK deca moraju nestati pre vlasnika."""
    cleanup_generic_owned_content(instance)
