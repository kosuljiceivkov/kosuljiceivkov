"""Blog-specific admin inlines — bez nested_admin zavisnosti."""

from django.contrib.contenttypes.admin import GenericStackedInline

from apps.seo.admin import SeoAnalyzerAdminMixin, SeoMetadataInline
from apps.seo.models import SeoMetadata
from apps.seo.services import get_seo_metadata


class BlogSeoMetadataInline(SeoAnalyzerAdminMixin, GenericStackedInline):
    """SEO panel u blog editor fioci — ista polja kao Projekti inline, bez ugnježdavanja."""

    model = SeoMetadata
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    max_num = 1
    can_delete = True
    classes = ("seo-metadata-inline", "blog-post-editor__seo-inline")
    verbose_name = "SEO"
    verbose_name_plural = "SEO"
    readonly_fields = SeoMetadataInline.readonly_fields
    fieldsets = SeoMetadataInline.fieldsets

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return 0
        return 0 if get_seo_metadata(obj) else 1
