"""Rutiranje CMS stranica — fiksne javne rute."""

from django.urls import reverse

from apps.layout.models import CMSPage

PROJEKTI_PAGE_ROUTE = {
    "url_name": "frontend:projekti",
    "template": "frontend/projekti.html",
    "preview_template": "frontend/projekti.html",
}


def get_page_route(page: CMSPage) -> dict[str, str]:
    return PROJEKTI_PAGE_ROUTE


def get_page_template(page: CMSPage, *, preview: bool = False) -> str:
    route = get_page_route(page)
    if preview:
        return route["preview_template"]
    return route["template"]


def get_page_public_url(page: CMSPage) -> str | None:
    if not page.is_active:
        return None
    return reverse("frontend:projekti")


def get_page_preview_url_name(page: CMSPage) -> str:
    return "frontend:admin_preview_cms"


def is_builder_host_instance(obj) -> bool:
    from apps.blog.models import BlogPost

    return isinstance(obj, (CMSPage, BlogPost))
