from django.conf import settings


def site_branding(request):
    """Logo, favicon and site name for templates and Django admin."""
    logo = getattr(settings, "SITE_ADMIN_BRAND_LOGO", "img/logo.webp")
    return {
        "site_admin_brand_name": getattr(
            settings, "SITE_ADMIN_BRAND_NAME", "Cementne košuljice Ivkov (admin)"
        ),
        "site_admin_brand_logo": logo,
        "site_favicon_webp": getattr(settings, "SITE_FAVICON_WEBP", logo),
        "site_favicon_png": getattr(settings, "SITE_FAVICON_PNG", "img/favicon.png"),
        "site_favicon_apple": getattr(
            settings, "SITE_FAVICON_APPLE", "img/apple-touch-icon.png"
        ),
    }
