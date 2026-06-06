"""
Registar FileField / ImageField polja u instaliranim aplikacijama.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from django.apps import apps
from django.db import models


@dataclass(frozen=True, slots=True)
class MediaFieldRef:
    model: type[models.Model]
    field: models.FileField

    @property
    def field_name(self) -> str:
        return self.field.name

    @property
    def model_label(self) -> str:
        return self.model._meta.label


@dataclass(frozen=True, slots=True)
class InstanceMediaFile:
    """Jedan medijski fajl vezan za instancu modela."""

    name: str
    storage: object
    field_name: str
    model_label: str


def normalize_media_name(name: str | None) -> str:
    if not name:
        return ""
    return str(name).replace("\\", "/").lstrip("/")


def storage_key(storage: object) -> str:
    """Stabilan ključ skladišta — ista R2 putanja = isti ključ."""
    location = getattr(storage, "location", "") or ""
    bucket = getattr(storage, "bucket_name", "") or ""
    backend = f"{storage.__class__.__module__}.{storage.__class__.__name__}"
    return f"{backend}|{bucket}|{location}"


def media_identity(name: str | None, storage: object) -> tuple[str, str] | None:
    normalized = normalize_media_name(name)
    if not normalized:
        return None
    return storage_key(storage), normalized


@lru_cache(maxsize=1)
def get_media_field_refs() -> tuple[MediaFieldRef, ...]:
    refs: list[MediaFieldRef] = []
    for model in apps.get_models():
        if model._meta.abstract or model._meta.proxy:
            continue
        for field in model._meta.get_fields():
            if isinstance(field, models.FileField):
                refs.append(MediaFieldRef(model=model, field=field))
    return tuple(refs)


def iter_instance_media_files(instance: models.Model) -> list[InstanceMediaFile]:
    """Sva ne-prazna File/Image polja na instanci."""
    files: list[InstanceMediaFile] = []
    model = instance.__class__
    for ref in get_media_field_refs():
        if ref.model is not model:
            continue
        field_file = getattr(instance, ref.field_name, None)
        name = getattr(field_file, "name", "") or ""
        normalized = normalize_media_name(name)
        if not normalized:
            continue
        storage = field_file.storage if field_file else ref.field.storage
        files.append(
            InstanceMediaFile(
                name=normalized,
                storage=storage,
                field_name=ref.field_name,
                model_label=ref.model_label,
            )
        )
    return files


def get_media_storage_aliases() -> tuple[str, ...]:
    """Sva Django STORAGES imena osim staticfiles."""
    from django.conf import settings

    aliases: list[str] = []
    for alias, config in settings.STORAGES.items():
        if alias == "staticfiles":
            continue
        backend = config.get("BACKEND", "")
        if "StaticFilesStorage" in backend or "CompressedManifestStaticFilesStorage" in backend:
            continue
        aliases.append(alias)
    return tuple(sorted(set(aliases)))
