from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from apps.seo.breadcrumbs import resolve_breadcrumb_trail
from apps.seo.json_ld import collect_json_ld_schemas
from apps.seo.rendering import resolve_seo_tags

register = template.Library()

_SEO_RENDER_FLAG = "seo_meta_rendered"


def _site_name(context) -> str:
    site_name = context.get("seo_site_name")
    if site_name:
        return site_name
    return getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")


@register.inclusion_tag("seo/head.html", takes_context=True)
def render_seo_meta(context, seo_object=None, og_type=None):
    """
    Renderuje kompletan SEO <head> blok (title, meta, canonical, robots,
    Open Graph, Twitter Card).

    Pozovite samo jednom po stranici — obično u base.html.
    Ponovljeni poziv ne renderuje duplikate.

    Primeri:
        {% render_seo_meta %}
        {% render_seo_meta seo_object %}
        {% render_seo_meta seo_object "article" %}
    """
    if context.get(_SEO_RENDER_FLAG):
        return {
            "skip_render": True,
            "seo": {},
            "seo_site_name": "",
            "request": context.get("request"),
        }

    context[_SEO_RENDER_FLAG] = True
    request = context.get("request")
    obj = seo_object if seo_object is not None else context.get("seo_object")
    resolved_og_type = og_type or context.get("seo_og_type")
    overrides = context.get("seo_overrides") or {}

    seo = resolve_seo_tags(
        request,
        seo_object=obj,
        og_type=resolved_og_type,
        overrides=overrides,
    )

    return {
        "skip_render": False,
        "seo": seo,
        "seo_site_name": _site_name(context),
        "request": request,
    }


@register.simple_tag(takes_context=True)
def resolve_seo(context, seo_object=None, og_type=None):
    """
    Vraća rečnik SEO vrednosti u kontekst (bez HTML).
    Korisno za debug ili prilagođene partial-e.

    Primer:
        {% resolve_seo post "article" as seo %}
        {{ seo.title }}
    """
    request = context.get("request")
    obj = seo_object if seo_object is not None else context.get("seo_object")
    resolved_og_type = og_type or context.get("seo_og_type")
    overrides = context.get("seo_overrides") or {}
    return resolve_seo_tags(
        request,
        seo_object=obj,
        og_type=resolved_og_type,
        overrides=overrides,
    )


@register.inclusion_tag("seo/json_ld.html", takes_context=True)
def render_json_ld(context, seo_object=None):
    """Renderuje validirane JSON-LD šeme za trenutnu stranicu."""
    request = context.get("request")
    obj = seo_object if seo_object is not None else context.get("seo_object")
    overrides = context.get("seo_overrides") or {}
    payloads = collect_json_ld_schemas(
        request,
        seo_object=obj,
        breadcrumbs_override=overrides.get("breadcrumbs"),
    )
    return {
        "json_ld_payloads": [mark_safe(payload) for payload in payloads],
    }


@register.inclusion_tag("partials/breadcrumbs.html", takes_context=True)
def render_breadcrumbs(context, seo_object=None):
    """Renderuje SEO breadcrumb navigaciju sa schema.org podrškom."""
    request = context.get("request")
    obj = seo_object if seo_object is not None else context.get("seo_object")
    overrides = context.get("breadcrumbs") or (context.get("seo_overrides") or {}).get("breadcrumbs")
    trail = resolve_breadcrumb_trail(
        request,
        seo_object=obj,
        breadcrumbs_override=overrides,
    )

    items = []
    for index, item in enumerate(trail.items):
        is_current = index == len(trail.items) - 1
        url = item.url
        if not url and item.url_name:
            from django.urls import reverse

            from apps.seo.schema.base import absolute_url

            try:
                path = reverse(item.url_name, kwargs=item.url_kwargs or None)
                url = absolute_url(request, path)
            except Exception:
                url = None
        if is_current:
            url = None

        items.append(
            {
                "title": item.title,
                "url": url,
                "is_current": is_current,
            }
        )

    return {
        "breadcrumb_items": items,
        "has_breadcrumbs": bool(items),
    }
