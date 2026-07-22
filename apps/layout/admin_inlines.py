"""Layout admin inlines — bez nested_admin zavisnosti."""

from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.contrib.contenttypes.models import ContentType

from apps.seo.admin import SeoAnalyzerAdminMixin, SeoMetadataInline
from apps.seo.models import SeoMetadata
from apps.seo.services import get_seo_metadata


class ProjektiSeoInlineFormSet(BaseGenericInlineFormSet):
    """Učitava SEO i za proxy (ProjektiPage) i za bazni CMSPage zapis."""

    def get_queryset(self):
        if self.instance._state.adding or not self.instance.pk:
            return self.model._default_manager.none()

        content_types = [
            ContentType.objects.get_for_model(self.instance, for_concrete_model=False),
            ContentType.objects.get_for_model(self.instance, for_concrete_model=True),
        ]
        return (
            self.model._default_manager.filter(
                object_id=self.instance.pk,
                content_type__in=content_types,
            )
            .select_related("content_type")
            .order_by("-pk")
        )


class ProjektiSeoMetadataInline(SeoAnalyzerAdminMixin, GenericStackedInline):
    """SEO panel u Projekti editor fioci."""

    model = SeoMetadata
    formset = ProjektiSeoInlineFormSet
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    max_num = 1
    can_delete = False
    template = "admin/seo/edit_inline/stacked_no_header.html"
    classes = ("seo-metadata-inline", "blog-post-editor__seo-inline")
    verbose_name = "SEO"
    verbose_name_plural = "SEO"
    readonly_fields = SeoMetadataInline.readonly_fields
    fieldsets = SeoMetadataInline.fieldsets

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return 0
        return 0 if get_seo_metadata(obj) else 1
