from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic.base import RedirectView

from apps.core.views import health_check
from apps.seo.sitemaps import sitemaps
from apps.seo.views import robots_txt

urlpatterns = [
    path("health/", health_check, name="health"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url(settings.SITE_FAVICON_PNG), permanent=True),
        name="favicon",
    ),
    path("admin/", admin.site.urls),
    path("robots.txt", robots_txt, name="robots"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="sitemap",
    ),
    path("", include("apps.frontend.urls")),
]

# Local media only in development (R2 in production)
if settings.DEBUG and not getattr(settings, "USE_R2_STORAGE", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
