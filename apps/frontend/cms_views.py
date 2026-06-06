from django.http import Http404
from django.shortcuts import render

from apps.blog.selectors import (
    get_active_category_by_path,
    get_published_post,
    get_published_posts_queryset,
)
from apps.layout.selectors import get_projekti_page
from apps.seo.page_seo import build_static_page_seo

BLOG_INDEX_SEO = {
    "title": "Blog",
    "description": (
        "Stručni saveti i vesti o pripremi podloge, ugradnji "
        "i održavanju cementnih košuljica."
    ),
}


def projekti(request):
    page = get_projekti_page()
    if page is None:
        raise Http404("Stranica projekata nije konfigurisana.")

    return render(
        request,
        "frontend/projekti.html",
        {
            "page": page,
            "seo_object": page,
        },
    )


def blog_list(request):
    posts = get_published_posts_queryset()
    return render(
        request,
        "frontend/blog_list.html",
        {
            "posts": posts,
            "seo_overrides": build_static_page_seo(
                request,
                url_name="frontend:blog",
                **BLOG_INDEX_SEO,
            ),
        },
    )


def blog_category(request, category_path):
    category = get_active_category_by_path(category_path)
    posts = get_published_posts_queryset(category=category)
    description = category.description.strip() or (
        f"Blog objave u kategoriji {category.get_breadcrumb_title()}."
    )
    return render(
        request,
        "frontend/blog_category.html",
        {
            "category": category,
            "posts": posts,
            "seo_object": category,
            "seo_overrides": build_static_page_seo(
                request,
                title=category.get_breadcrumb_title(),
                description=description,
                url_name="frontend:blog_category",
                url_kwargs={"category_path": category.get_slug_path()},
                og_type="website",
            ),
        },
    )


def blog_detail(request, slug):
    post = get_published_post(slug)
    return render(
        request,
        "frontend/blog_detail.html",
        {
            "post": post,
            "seo_object": post,
            "seo_og_type": "article",
        },
    )
