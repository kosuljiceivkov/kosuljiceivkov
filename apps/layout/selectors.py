"""Upiti za CMS stranice."""

from apps.layout.models import CMSPage

PROJEKTI_PAGE_FIELDS = (
    "id",
    "title",
    "slug",
    "page_type",
    "is_active",
    "updated_at",
)


def get_projekti_page():
    return (
        CMSPage.objects.filter(
            page_type=CMSPage.PageType.PROJEKTI,
            is_active=True,
        )
        .prefetch_related("seo_metadata")
        .only(*PROJEKTI_PAGE_FIELDS)
        .first()
    )
