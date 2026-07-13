from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from apps.blog.admin_api.page_catalog import page_builder_catalog_view
from apps.layout.admin_api import (
    page_cleanup_pending_media_view,
    page_save_view,
    page_upload_image_view,
    page_upload_video_view,
)
from apps.layout.admin_change import build_projekti_change_form_context
from apps.layout.admin_inlines import ProjektiSeoMetadataInline
from apps.layout.admin_preview_links import get_admin_preview_url
from apps.layout.forms import ProjektiPageAdminForm

from .models import CMSPage, ProjektiPage


@admin.register(ProjektiPage)
class ProjektiPageAdmin(admin.ModelAdmin):
    """Visual builder editor za stranicu /projekti/."""

    change_form_template = "admin/layout/projektipage/change_form.html"
    form = ProjektiPageAdminForm
    inlines = [ProjektiSeoMetadataInline]
    readonly_fields = (
        "public_url_display",
        "created_at",
        "updated_at",
    )
    view_on_site = True

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            page_type=CMSPage.PageType.PROJEKTI
        )

    def get_fields(self, request, obj=None):
        return ("title", "is_active")

    def get_fieldsets(self, request, obj=None):
        return ()

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

    def get_view_on_site_url(self, obj):
        return get_admin_preview_url(obj)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "title":
            kwargs.setdefault(
                "widget",
                admin.widgets.AdminTextareaWidget(
                    attrs={
                        "class": "blog-post-editor__title-input",
                        "placeholder": "Naslov stranice",
                        "id": "blog-post-title-input",
                        "autocomplete": "off",
                        "rows": 1,
                    }
                ),
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None:
            extra_context.update(build_projekti_change_form_context(request, obj))
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        obj.page_type = CMSPage.PageType.PROJEKTI
        obj.slug = "projekti"
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:page_id>/page/save/",
                self.admin_site.admin_view(page_save_view),
                name="layout_projektipage_page_save",
            ),
            path(
                "<int:page_id>/page/upload-image/",
                self.admin_site.admin_view(page_upload_image_view),
                name="layout_projektipage_page_upload_image",
            ),
            path(
                "<int:page_id>/page/upload-video/",
                self.admin_site.admin_view(page_upload_video_view),
                name="layout_projektipage_page_upload_video",
            ),
            path(
                "<int:page_id>/page/cleanup-pending-media/",
                self.admin_site.admin_view(page_cleanup_pending_media_view),
                name="layout_projektipage_page_cleanup_pending_media",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Javna adresa")
    def public_url_display(self, obj):
        return format_html(
            '<a href="/projekti/" target="_blank" rel="noopener noreferrer">/projekti/</a>'
        )
