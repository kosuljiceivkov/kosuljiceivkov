"""Upiti za blog objave — centralizovano za performanse."""

from django.shortcuts import get_object_or_404

from apps.blog.models import BlogCategory, BlogPost

PUBLISHED_POST_LIST_FIELDS = (
    "id",
    "title",
    "slug",
    "excerpt",
    "publish_date",
    "featured_image",
    "updated_at",
    "category_id",
)

PUBLISHED_POST_DETAIL_FIELDS = PUBLISHED_POST_LIST_FIELDS + (
    "body_page",
    "body_plaintext",
    "page_version",
)


def get_published_posts_queryset(*, category=None):
    queryset = (
        BlogPost.objects.publicly_visible()
        .select_related("category", "category__parent")
        .prefetch_related("seo_metadata")
        .only(*PUBLISHED_POST_LIST_FIELDS)
        .order_by("-publish_date", "-created_at")
    )
    if category is None:
        return queryset

    category_ids = [category.pk, *category.get_descendant_ids()]
    return queryset.filter(category_id__in=category_ids)


def get_latest_published_posts(limit=3):
    return list(get_published_posts_queryset()[:limit])


def get_published_post(slug):
    return get_object_or_404(
        BlogPost.objects.publicly_visible()
        .select_related("category", "category__parent")
        .prefetch_related("seo_metadata")
        .only(*PUBLISHED_POST_DETAIL_FIELDS),
        slug=slug,
    )


def get_active_category_by_path(category_path: str) -> BlogCategory:
    slugs = [part for part in category_path.strip("/").split("/") if part]
    if not slugs:
        raise BlogCategory.DoesNotExist

    parent = None
    category = None
    for slug in slugs:
        category = get_object_or_404(
            BlogCategory.objects.active().select_related("parent"),
            slug=slug,
            parent=parent,
        )
        parent = category
    return category
