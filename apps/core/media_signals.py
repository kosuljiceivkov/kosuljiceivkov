"""
Django signali za automatsko čišćenje medijskih fajlova pri brisanju i zameni.
"""
from __future__ import annotations

from django.db.models import signals

from apps.core.media_cleanup_service import (
    _OLD_FILES_ATTR,
    capture_previous_media_files,
    cleanup_instance_files,
    cleanup_replaced_files,
    schedule_media_cleanup,
)
from apps.core.media_registry import get_media_field_refs, iter_instance_media_files


def _on_pre_save(sender, instance, **kwargs):
    capture_previous_media_files(instance)


def _on_post_save(sender, instance, **kwargs):
    old_files = getattr(instance, _OLD_FILES_ATTR, ())
    new_files = tuple(iter_instance_media_files(instance))

    def _cleanup_replaced():
        cleanup_replaced_files(old_files, new_files)

    schedule_media_cleanup(_cleanup_replaced)


def _on_post_delete(sender, instance, **kwargs):
    def _cleanup_deleted():
        cleanup_instance_files(instance, reason="instance_deleted")

    schedule_media_cleanup(_cleanup_deleted)


_signals_connected = False


def connect_media_cleanup_signals() -> None:
    """Povezuje signale na sve modele sa FileField / ImageField."""
    global _signals_connected
    if _signals_connected:
        return
    _signals_connected = True

    connected: set[str] = set()
    for ref in get_media_field_refs():
        label = ref.model_label
        if label in connected:
            continue
        connected.add(label)

        signals.pre_save.connect(_on_pre_save, sender=ref.model, weak=False)
        signals.post_save.connect(_on_post_save, sender=ref.model, weak=False)
        signals.post_delete.connect(_on_post_delete, sender=ref.model, weak=False)
