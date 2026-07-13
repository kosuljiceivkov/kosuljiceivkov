"""
Signali za automatsko brisanje GenericForeignKey sadržaja (SEO) i JSON medija.
"""
from __future__ import annotations

from django.db.models import signals

from apps.core.generic_cleanup import (
    cleanup_generic_owned_content_before_delete,
    iter_generic_content_owner_models,
)

_signals_connected = False


def _on_owner_pre_delete(sender, instance, **kwargs):
    cleanup_generic_owned_content_before_delete(instance)


def connect_generic_cleanup_signals() -> None:
    """Povezuje pre_delete na modele sa seo_metadata."""
    global _signals_connected
    if _signals_connected:
        return
    _signals_connected = True

    connected: set[str] = set()
    for model in iter_generic_content_owner_models():
        label = model._meta.label
        if label in connected:
            continue
        connected.add(label)
        signals.pre_delete.connect(
            _on_owner_pre_delete,
            sender=model,
            weak=False,
        )
