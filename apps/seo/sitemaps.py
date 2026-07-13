from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.seo.sitemap_filters import exclude_seo_hidden


class StaticViewSitemap(Sitemap):
    """Statične Django stranice."""

    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["home", "usluge", "kontakt", "projekti", "blog"]

    def location(self, item):
        return reverse(f"frontend:{item}")


class BlogPostSitemap(Sitemap):
    """Objavljene blog objave."""

    changefreq = "weekly"
    priority = 0.7

    def items(self):
        queryset = (
            BlogPost.objects.publicly_visible()
            .only("slug", "updated_at", "publish_date")
            .order_by("-publish_date", "-created_at")
        )
        return exclude_seo_hidden(queryset, BlogPost)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CMSPageSitemap(Sitemap):
    """Aktivne CMS stranice sa javnom rutom."""

    changefreq = "weekly"
    priority = 0.7

    def items(self):
        from apps.layout.models import CMSPage

        pages = (
            CMSPage.objects.filter(is_active=True)
            .only("slug", "page_type", "updated_at")
            .order_by("title")
        )
        pages = exclude_seo_hidden(pages, CMSPage)
        return [page for page in pages if page.get_absolute_url()]

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


sitemaps = {
    "static": StaticViewSitemap,
    "blog": BlogPostSitemap,
    "cms": CMSPageSitemap,
}
