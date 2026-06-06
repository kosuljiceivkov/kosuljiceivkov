from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampMixin(models.Model):
    """Zajednička polja za vreme kreiranja i izmene."""

    created_at = models.DateTimeField("Kreirano", auto_now_add=True)
    updated_at = models.DateTimeField("Ažurirano", auto_now=True)

    class Meta:
        abstract = True


class SeoContentMixin(models.Model):
    """
    SEO interfejs za CMS modele — podaci žive u apps.seo.models.SeoMetadata.
    Kompatibilno sa {% render_seo_meta %} preko get_seo_context().
    """

    class Meta:
        abstract = True

    def get_seo_fallback_title(self):
        from apps.seo.services import get_seo_fallback_title

        return get_seo_fallback_title(self)

    def get_seo_fallback_description(self):
        from apps.seo.services import get_seo_fallback_description

        return get_seo_fallback_description(self)

    def get_seo_title(self):
        from apps.seo.services import resolve_seo_title

        return resolve_seo_title(self)

    def get_seo_description(self):
        from apps.seo.services import resolve_meta_description

        return resolve_meta_description(self)

    def get_seo_fallback_canonical_path(self):
        from apps.seo.services import get_seo_fallback_canonical_path

        return get_seo_fallback_canonical_path(self)

    def get_canonical_url(self, request):
        from apps.seo.services import resolve_canonical_url

        return resolve_canonical_url(self, request)

    @staticmethod
    def resolve_absolute_url(request, url):
        from apps.seo.helpers import resolve_absolute_url

        return resolve_absolute_url(request, url)

    def get_breadcrumb_title(self):
        from apps.seo.services import resolve_breadcrumb_title

        return resolve_breadcrumb_title(self)

    def get_schema_type(self):
        from apps.seo.services import get_seo_metadata, resolve_schema_type

        return resolve_schema_type(self, get_seo_metadata(self))

    def get_seo_context(self, request=None, *, og_type="website"):
        from apps.seo.services import build_seo_context

        return build_seo_context(self, request, og_type=og_type)


# Backward-compatible alias for imports across the project.
CMSMetaMixin = SeoContentMixin
