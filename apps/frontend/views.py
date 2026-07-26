from django.shortcuts import render
from django.views.decorators.cache import cache_page

from apps.blog.selectors import get_latest_published_posts
from apps.seo.page_seo import build_static_page_seo

from .home_data import (
    ABOUT_SCREED,
    HOME_FAQ_ITEMS,
    HOME_PROJECT_HIGHLIGHTS,
    HOME_SEO_DESCRIPTION,
    HOME_SEO_TITLE,
    MACHINE_SCREED_ADVANTAGES,
    PRICE_SECTION,
    PROCESS_STEPS,
    SCREED_TYPES,
)
from .landing_data import (
    LANDING_CENA,
    LANDING_CEMENTNE_KOSULJICE,
    LANDING_ESTRIH,
)
from .services_data import AUDIENCE, QUALITY_SECTION, SERVICES
from .static_media_data import SERVICES_GALLERY_IMAGES, WORK_CAROUSEL_SLIDES

_STATIC_PAGE_CACHE = 60 * 5


def _render_landing(request, landing: dict):
    url_name = landing["url_name"]
    return render(
        request,
        "frontend/landing.html",
        {
            "landing": landing,
            "seo_overrides": build_static_page_seo(
                request,
                title=landing["seo_title"],
                description=landing["seo_description"],
                url_name=url_name,
            ),
        },
    )


@cache_page(_STATIC_PAGE_CACHE)
def home(request):
    return render(
        request,
        "frontend/home.html",
        {
            "services_preview": SERVICES,
            "latest_posts": get_latest_published_posts(limit=3),
            "machine_screed_advantages": MACHINE_SCREED_ADVANTAGES,
            "about_screed": ABOUT_SCREED,
            "screed_types": SCREED_TYPES,
            "price_section": PRICE_SECTION,
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
            "about_screed": ABOUT_SCREED,
            "screed_types": SCREED_TYPES,
            "price_section": PRICE_SECTION,
            "seo_overrides": {
                "title": "Cementne košuljice — usluge",
                "description": (
                    "Usluge cementnih košuljica: mašinska izrada, laserska "
                    "nivelacija poda i termo i zvučna izolacija. Estrih spreman "
                    "za završne obloge — zatražite ponudu."
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
                "title": "Kontakt — cementne košuljice",
                "description": (
                    "Kontakt za cementne košuljice: pozovite nas za procenu i "
                    "ponudu mašinske izrade estriha širom Srbije."
                ),
            },
        },
    )


@cache_page(_STATIC_PAGE_CACHE)
def cementne_kosuljice(request):
    return _render_landing(request, LANDING_CEMENTNE_KOSULJICE)


@cache_page(_STATIC_PAGE_CACHE)
def cena_cementne_kosuljice(request):
    return _render_landing(request, LANDING_CENA)


@cache_page(_STATIC_PAGE_CACHE)
def estrih(request):
    return _render_landing(request, LANDING_ESTRIH)
