"""Upiti za CMS stranice."""

from apps.layout.models import CMSPage

PROJEKTI_PAGE_FIELDS = (
    "id",
    "title",
    "slug",
    "page_type",
    "is_active",
    "meta_title",
    "meta_description",
    "updated_at",
)


def get_projekti_page():
    return (
        CMSPage.objects.filter(
            page_type=CMSPage.PageType.PROJEKTI,
            is_active=True,
        )
        .only(*PROJEKTI_PAGE_FIELDS)
        .first()
    )
