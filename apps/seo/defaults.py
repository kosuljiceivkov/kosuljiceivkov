from django.conf import settings


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
    canonical = None
    if request:
        canonical = request.build_absolute_uri(request.path)

    og_image = getattr(settings, "SEO_DEFAULT_OG_IMAGE_URL", None)
    if og_image and request and og_image.startswith("/"):
        og_image = request.build_absolute_uri(og_image)

    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "robots": "index, follow",
        "keywords": getattr(settings, "SEO_DEFAULT_KEYWORDS", ""),
        "focus_keyword": "",
        "og_type": "website",
        "og_title": title,
        "og_description": description,
        "og_image": og_image,
        "twitter_card": "summary_large_image" if og_image else "summary",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": og_image,
    }
