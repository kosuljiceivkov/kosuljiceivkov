"""Fragment keš za renderovani page builder HTML."""

from django.conf import settings
from django.core.cache import cache

from apps.layout.contenttypes import get_content_type_for_model

BUILDER_VERSION_PREFIX = "builder:v:"
BUILDER_HTML_PREFIX = "builder:html:"


def _host_key(content_type_id: int, object_id: int) -> str:
    return f"{content_type_id}:{object_id}"


def get_builder_cache_version(content_type_id: int, object_id: int) -> int:
    key = BUILDER_VERSION_PREFIX + _host_key(content_type_id, object_id)
    return cache.get(key, 0)


def bump_builder_cache_version(content_type_id: int, object_id: int) -> int:
    key = BUILDER_VERSION_PREFIX + _host_key(content_type_id, object_id)
    version = cache.get(key, 0) + 1
    cache.set(key, version, timeout=None)
    return version


def invalidate_builder_cache_for_host(content_type_id: int, object_id: int) -> None:
    """Povećava verziju keša — stari HTML fragmenti postaju nevažeći."""
    bump_builder_cache_version(content_type_id, object_id)


def invalidate_builder_cache_for_page(page_object) -> None:
    if page_object is None or not page_object.pk:
        return
    content_type = get_content_type_for_model(page_object.__class__)
    invalidate_builder_cache_for_host(content_type.id, page_object.pk)


def make_builder_html_cache_key(page_object, visible_only: bool, version: int | None = None) -> str:
    content_type = get_content_type_for_model(page_object.__class__)
    if version is None:
        version = get_builder_cache_version(content_type.id, page_object.pk)
    visibility = "1" if visible_only else "0"
    return (
        f"{BUILDER_HTML_PREFIX}{content_type.id}:{page_object.pk}:{visibility}:{version}"
    )


def get_cached_builder_html(page_object, visible_only: bool):
    if page_object is None or not page_object.pk:
        return None
    key = make_builder_html_cache_key(page_object, visible_only)
    return cache.get(key)


def set_cached_builder_html(page_object, visible_only: bool, html: str) -> None:
    timeout = getattr(settings, "BUILDER_CACHE_TIMEOUT", 3600)
    key = make_builder_html_cache_key(page_object, visible_only)
    cache.set(key, html, timeout)
