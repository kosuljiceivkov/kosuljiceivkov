"""Admin pregled stranica sa builderom."""

from django.urls import reverse

from apps.blog.models import BlogPost
from apps.layout.cms_routing import get_page_preview_url_name
from apps.layout.models import CMSPage


def get_admin_preview_url(obj):
    """Staff pregled stranice/objave sa builderom."""
    if obj is None or not getattr(obj, "pk", None):
        return None
    if isinstance(obj, BlogPost):
        return reverse("frontend:admin_preview_blog", args=[obj.pk])
    if isinstance(obj, CMSPage):
        return reverse(get_page_preview_url_name(obj), args=[obj.pk])
    return None
