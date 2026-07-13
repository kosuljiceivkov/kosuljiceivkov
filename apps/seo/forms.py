"""SEO admin forme — prijateljski UI iznad robots polja u bazi."""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.seo.models import SeoMetadata

SEARCH_ENGINE_VISIBILITY_CHOICES = (
    (True, _("Prikaži u Google-u (index, follow)")),
    (False, _("Sakrij od Google-a (noindex, nofollow)")),
)


class SeoMetadataAdminForm(forms.ModelForm):
    """Zamenjuje robots_index/robots_follow checkboxe jednostavnim izborom."""

    class Meta:
        model = SeoMetadata
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["robots_index"].label = _("Vidljivost u pretrazi")
        self.fields["robots_index"].widget = forms.RadioSelect(
            choices=SEARCH_ENGINE_VISIBILITY_CHOICES,
        )
        self.fields["robots_index"].help_text = _(
            "Koristite „Sakrij od Google-a” za stranice koje ne želite u rezultatima pretrage."
        )
        self.fields["robots_follow"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        allow_indexing = cleaned_data.get("robots_index", True)
        cleaned_data["robots_follow"] = allow_indexing
        if not allow_indexing:
            cleaned_data["include_in_sitemap"] = False
        return cleaned_data
