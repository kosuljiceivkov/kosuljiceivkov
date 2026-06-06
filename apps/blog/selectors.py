"""Upiti za blog objave — centralizovano za performanse."""

from django.shortcuts import get_object_or_404

from apps.blog.models import BlogPost

PUBLISHED_POST_FIELDS = (
    "id",
    "title",
    "slug",
    "excerpt",
    "publish_date",
    "featured_image",
    "meta_title",
    "meta_description",
    "updated_at",
)


def get_published_posts_queryset():
    return (
        BlogPost.objects.publicly_visible()
        .only(*PUBLISHED_POST_FIELDS)
        .order_by("-publish_date", "-created_at")
    )


def get_latest_published_posts(limit=3):
    return list(get_published_posts_queryset()[:limit])


def get_published_post(slug):
    return get_object_or_404(
        BlogPost.objects.publicly_visible().only(*PUBLISHED_POST_FIELDS),
        slug=slug,
    )
