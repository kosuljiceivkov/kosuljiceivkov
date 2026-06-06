"""Keširani ContentType upiti za page builder."""

from django.contrib.contenttypes.models import ContentType

_MODEL_CONTENT_TYPE_CACHE: dict[type, ContentType] = {}


def get_content_type_for_model(model) -> ContentType:
    """Vraća ContentType za model sa in-process kešom."""
    if model not in _MODEL_CONTENT_TYPE_CACHE:
        _MODEL_CONTENT_TYPE_CACHE[model] = ContentType.objects.get_for_model(model)
    return _MODEL_CONTENT_TYPE_CACHE[model]


def get_content_type_id_for_model(model) -> int:
    return get_content_type_for_model(model).id
