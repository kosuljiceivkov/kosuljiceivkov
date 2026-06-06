from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
import nested_admin

from apps.layout.builder_page_admin import (
    BUILDER_HISTORY_FIELDSET,
    BUILDER_SECTIONS_HINT,
    BUILDER_SEO_HINT,
    BuilderHostAdminMixin,
)
from apps.layout.forms import ProjektiPageAdminForm

from .models import CMSPage, ProjektiPage


@admin.register(ProjektiPage)
class ProjektiPageAdmin(BuilderHostAdminMixin, nested_admin.NestedModelAdmin, admin.ModelAdmin):
    """Editor stranice /projekti/."""

    form = ProjektiPageAdminForm
    readonly_fields = (
        "public_url_display",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": ("title", "public_url_display", "is_active"),
                "description": (
                    "Stranica projekata na sajtu. Javna adresa je uvek /projekti/. "
                    + BUILDER_SECTIONS_HINT
                    + " "
                    + BUILDER_SEO_HINT
                ),
            },
        ),
        BUILDER_HISTORY_FIELDSET,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            page_type=CMSPage.PageType.PROJEKTI
        )

    def changelist_view(self, request, extra_context=None):
        page, _ = CMSPage.objects.get_or_create(
            page_type=CMSPage.PageType.PROJEKTI,
            defaults={
                "title": "Projekti",
                "slug": "projekti",
                "is_active": True,
            },
        )
        if page.slug != "projekti":
            page.slug = "projekti"
            page.save(update_fields=["slug"])
        return redirect(
            reverse("admin:layout_projektipage_change", args=[page.pk])
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.page_type = CMSPage.PageType.PROJEKTI
        obj.slug = "projekti"
        super().save_model(request, obj, form, change)

    @admin.display(description="Javna adresa")
    def public_url_display(self, obj):
        return format_html(
            '<a href="/projekti/" target="_blank" rel="noopener noreferrer">/projekti/</a>'
        )
