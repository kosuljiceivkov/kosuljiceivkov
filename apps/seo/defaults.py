from django.conf import settings

from apps.seo.canonical import resolve_request_canonical


def get_site_seo_defaults(request=None):
    """Podrazumevani SEO kada stranica nema seo_object."""
    site_name = getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")
    title = getattr(
        settings,
        "SEO_DEFAULT_TITLE",
        f"{site_name} — Cementne i betonske košuljice",
    )
    description = getattr(
        settings,
        "SEO_DEFAULT_DESCRIPTION",
        "Izrada i ugradnja cementnih i betonskih košuljica.",
    )
    canonical = resolve_request_canonical(request) if request else None

    og_image = getattr(settings, "SEO_DEFAULT_OG_IMAGE_URL", None)
    if og_image and request and og_image.startswith("/"):
        from apps.seo.canonical import build_absolute_canonical

        og_image = build_absolute_canonical(og_image, request)

    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "og_url": canonical,
        "robots": "index, follow",
        "og_type": "website",
        "og_title": title,
        "og_description": description,
        "og_image": og_image,
        "twitter_card": "summary_large_image" if og_image else "summary",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": og_image,
    }
