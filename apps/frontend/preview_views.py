"""Pregled renderovanog sadržaja za urednike (samo staff)."""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from apps.layout.cms_routing import get_page_template
from apps.layout.models import CMSPage


@staff_member_required
def preview_cms_page(request, pk):
    page = get_object_or_404(CMSPage, pk=pk)
    template_name = get_page_template(page, preview=True)

    return render(
        request,
        template_name,
        {
            "page": page,
            "seo_object": page,
            "is_admin_preview": True,
            "builder_visible_only": False,
            "preview_mode": True,
            "is_draft_preview": not page.is_active,
        },
    )


@staff_member_required
def preview_blog_post(request, pk):
    from apps.blog.models import BlogPost

    post = get_object_or_404(BlogPost, pk=pk)
    return render(
        request,
        "frontend/blog_detail.html",
        {
            "post": post,
            "seo_object": post,
            "seo_og_type": "article",
            "is_admin_preview": True,
            "builder_visible_only": False,
            "preview_mode": True,
            "is_draft_preview": not post.is_published,
        },
    )
