from django import template
from django.utils.safestring import mark_safe

from apps.seo.defaults import get_site_seo_defaults
from apps.seo.json_ld import collect_json_ld_schemas

register = template.Library()


@register.inclusion_tag("seo/meta_tags.html", takes_context=True)
def render_seo_meta(context, seo_object=None, og_type=None):
    """
    Renderuje meta, Open Graph i Twitter tagove.
    Prosledi seo_object (model sa get_seo_context) ili koristi podrazumevano.
    """
    request = context.get("request")
    obj = seo_object or context.get("seo_object")

    if obj is not None and hasattr(obj, "get_seo_context"):
        resolved_og_type = og_type or context.get("seo_og_type", "website")
        seo = obj.get_seo_context(request, og_type=resolved_og_type)
    else:
        seo = get_site_seo_defaults(request)
        if og_type:
            seo["og_type"] = og_type

    overrides = context.get("seo_overrides") or {}
    for key, value in overrides.items():
        if value:
            seo[key] = value
            if key == "title":
                seo.setdefault("og_title", value)
                seo.setdefault("twitter_title", value)
            if key == "description":
                seo.setdefault("og_description", value)
                seo.setdefault("twitter_description", value)

    site_name = context.get("seo_site_name")
    if not site_name:
        from django.conf import settings

        site_name = getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")

    return {
        "seo": seo,
        "seo_site_name": site_name,
        "request": request,
    }


@register.inclusion_tag("seo/json_ld.html", takes_context=True)
def render_json_ld(context, seo_object=None):
    """Renderuje validirane JSON-LD šeme za trenutnu stranicu."""
    request = context.get("request")
    obj = seo_object or context.get("seo_object")
    payloads = collect_json_ld_schemas(request, seo_object=obj)
    return {
        "json_ld_payloads": [mark_safe(payload) for payload in payloads],
    }
