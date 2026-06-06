from django.shortcuts import render
from django.views.decorators.cache import cache_page

from apps.blog.selectors import get_latest_published_posts

from .home_data import (
    HOME_FAQ_ITEMS,
    HOME_PROJECT_HIGHLIGHTS,
    HOME_SEO_DESCRIPTION,
    HOME_SEO_TITLE,
    MACHINE_SCREED_ADVANTAGES,
    PROCESS_STEPS,
)
from .services_data import AUDIENCE, QUALITY_SECTION, SERVICES
from .static_media_data import SERVICES_GALLERY_IMAGES, WORK_CAROUSEL_SLIDES

_STATIC_PAGE_CACHE = 60 * 5


@cache_page(_STATIC_PAGE_CACHE)
def home(request):
    return render(
        request,
        "frontend/home.html",
        {
            "services_preview": SERVICES,
            "latest_posts": get_latest_published_posts(limit=3),
            "machine_screed_advantages": MACHINE_SCREED_ADVANTAGES,
            "process_steps": PROCESS_STEPS,
            "work_carousel_slides": WORK_CAROUSEL_SLIDES,
            "project_highlights": HOME_PROJECT_HIGHLIGHTS,
            "home_faq_items": HOME_FAQ_ITEMS,
            "seo_overrides": {
                "title": HOME_SEO_TITLE,
                "description": HOME_SEO_DESCRIPTION,
            },
        },
    )


@cache_page(_STATIC_PAGE_CACHE)
def usluge(request):
    return render(
        request,
        "frontend/usluge.html",
        {
            "services": SERVICES,
            "audience": AUDIENCE,
            "quality_section": QUALITY_SECTION,
            "gallery_images": SERVICES_GALLERY_IMAGES,
            "seo_overrides": {
                "title": "Usluge",
                "description": (
                    "Mašinska izrada cementnih košuljica, laserska nivelacija "
                    "poda i termo i zvučna izolacija."
                ),
            },
        },
    )


@cache_page(_STATIC_PAGE_CACHE)
def kontakt(request):
    return render(
        request,
        "frontend/kontakt.html",
        {
            "seo_overrides": {
                "title": "Kontakt",
                "description": (
                    "Pozovite nas za procenu i ponudu — mašinska izrada "
                    "cementnih košuljica."
                ),
            },
        },
    )
