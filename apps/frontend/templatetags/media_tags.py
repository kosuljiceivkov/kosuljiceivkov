"""Responsive image helpers for templates."""

from django import template

register = template.Library()

DEFAULT_SIZES = "(max-width: 767px) 100vw, min(100vw, 960px)"
CARD_SIZES = "(max-width: 767px) 100vw, (max-width: 1024px) 50vw, 400px"
CAROUSEL_SIZES = "100vw"


def build_responsive_image_context(
    image_field,
    *,
    alt="",
    css_class="",
    sizes=DEFAULT_SIZES,
    loading="lazy",
    fetchpriority="",
):
    if not image_field or not getattr(image_field, "name", ""):
        return None

    width = getattr(image_field, "width", None) or None
    height = getattr(image_field, "height", None) or None
    url = image_field.url
    srcset = f"{url} {width}w" if width else ""

    return {
        "src": url,
        "srcset": srcset,
        "sizes": sizes if srcset else "",
        "alt": alt,
        "css_class": css_class,
        "width": width,
        "height": height,
        "loading": loading,
        "fetchpriority": fetchpriority,
    }


@register.inclusion_tag("partials/responsive_image.html")
def responsive_image(
    image_field,
    alt="",
    css_class="",
    sizes=DEFAULT_SIZES,
    loading="lazy",
    fetchpriority="",
):
    context = build_responsive_image_context(
        image_field,
        alt=alt,
        css_class=css_class,
        sizes=sizes,
        loading=loading,
        fetchpriority=fetchpriority,
    )
    return {"image": context}
