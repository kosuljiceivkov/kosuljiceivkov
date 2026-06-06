from django.conf import settings


def seo_site(request):
    return {
        "seo_site_name": getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov"),
    }
