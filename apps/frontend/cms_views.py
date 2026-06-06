from django.http import Http404
from django.shortcuts import render

from apps.blog.selectors import get_published_post, get_published_posts_queryset
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
