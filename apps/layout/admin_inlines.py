"""Layout admin inlines — bez nested_admin zavisnosti."""

from django.contrib.contenttypes.admin import GenericStackedInline

from apps.seo.admin import SeoAnalyzerAdminMixin, SeoMetadataInline
from apps.seo.models import SeoMetadata


class ProjektiSeoMetadataInline(SeoAnalyzerAdminMixin, GenericStackedInline):
    """SEO panel u Projekti editor fioci."""

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
