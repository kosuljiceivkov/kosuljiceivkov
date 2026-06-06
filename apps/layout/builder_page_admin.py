"""Zajednički admin za stranice sa page builderom (Projekti, Blog)."""

from django.contrib.admin.options import ShowFacets

from apps.layout.admin_preview_links import get_admin_preview_url
from apps.layout.builder_admin import BuilderAdminMixin

BUILDER_SEO_FIELDSET = (
    "SEO",
    {
        "fields": ("meta_title", "meta_description", "canonical_url"),
        "description": (
            "Meta podaci za Google. Kanonski URL ostavite prazan "
            "za automatsko generisanje."
        ),
    },
)

BUILDER_HISTORY_FIELDSET = (
    "Istorija",
    {"fields": ("created_at", "updated_at")},
)

BUILDER_SECTIONS_HINT = (
    "Sadržaj gradite u sekcijama ispod. "
    'Za pregled koristite „Pregled na sajtu” gore desno.'
)


class BuilderHostAdminMixin(BuilderAdminMixin):
    """Isti page builder i pregled na sajtu za Projekti i Blog."""

    view_on_site = True
    list_filter = ()
    date_hierarchy = None
    show_facets = ShowFacets.NEVER

    def get_view_on_site_url(self, obj):
        return get_admin_preview_url(obj)
