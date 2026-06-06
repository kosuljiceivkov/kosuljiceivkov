"""SEO pomoćnici za statične Django stranice."""

from django.urls import reverse


def build_static_page_seo(request, *, title, description, url_name, og_type="website"):
    """
    Kreira seo_overrides rečnik sa kanonskim URL-om i Open Graph poljima.
    """
    path = reverse(url_name)
    canonical = request.build_absolute_uri(path) if request else None
    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "og_type": og_type,
        "og_title": title,
        "og_description": description,
        "twitter_title": title,
        "twitter_description": description,
    }
