from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from apps.layout.admin_preview_links import get_admin_preview_url

from .admin_api import (
    page_builder_catalog_view,
    page_cleanup_pending_media_view,
    page_save_view,
    page_upload_image_view,
    page_upload_video_view,
)
from .admin_change import (
    DRAFT_SLUG_PREFIX,
    build_blog_change_form_context,
    create_visual_builder_draft,
    maybe_update_slug_from_title,
)
from .admin_forms import BlogPostAdminForm
from .admin_inlines import BlogSeoMetadataInline
from .models import BlogCategory, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "updated_at")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "breadcrumb_title")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "parent",
                    "breadcrumb_title",
                    "description",
                    "is_active",
                ),
            },
        ),
    )


@admin.action(description="Objavi izabrane objave")
def publish_posts(modeladmin, request, queryset):
    updated = queryset.update(is_published=True)
    modeladmin.message_user(
        request,
        f"Objavljeno objava: {updated}.",
        messages.SUCCESS,
    )


@admin.action(description="Povuci izabrane objave (sakrij sa sajta)")
def unpublish_posts(modeladmin, request, queryset):
    updated = queryset.update(is_published=False)
    modeladmin.message_user(
        request,
        f"Povučeno objava: {updated}.",
        messages.WARNING,
    )


_BLOG_FORM_FIELDS = (
    "title",
    "slug",
    "category",
    "excerpt",
    "featured_image",
    "publish_date",
    "is_published",
)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    change_form_template = "admin/blog/blogpost/change_form.html"
    inlines = [BlogSeoMetadataInline]
    list_display = ("title", "slug", "category", "publish_date", "publish_status", "updated_at")
    search_fields = ("title", "slug", "excerpt", "seo_metadata__focus_keyword")
    list_filter = ("is_published", "category")
    readonly_fields = ("created_at", "updated_at")
    actions = [publish_posts, unpublish_posts]
    view_on_site = True

    def get_form(self, request, obj=None, change=False, **kwargs):
        fields = kwargs.get("fields")
        if fields is not None and len(fields) == 0 and obj is not None:
            kwargs["fields"] = list(_BLOG_FORM_FIELDS)
        kwargs.setdefault("form", BlogPostAdminForm)
        return super().get_form(request, obj, change=change, **kwargs)

    def get_fields(self, request, obj=None):
        return _BLOG_FORM_FIELDS

    def get_fieldsets(self, request, obj=None):
        return ()

    def get_prepopulated_fields(self, request, obj=None):
        return {}

    @admin.display(description="Status", boolean=True)
    def publish_status(self, obj):
        return obj.is_published

    def get_view_on_site_url(self, obj):
        return get_admin_preview_url(obj)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "title":
            kwargs.setdefault(
                "widget",
                admin.widgets.AdminTextareaWidget(
                    attrs={
                        "class": "blog-post-editor__title-input",
                        "placeholder": "Bez naslova",
                        "id": "blog-post-title-input",
                        "autocomplete": "off",
                        "rows": 1,
                    }
                ),
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def add_view(self, request, form_url="", extra_context=None):
        if not self.has_add_permission(request):
            raise PermissionDenied

        draft = create_visual_builder_draft()
        return HttpResponseRedirect(
            reverse("admin:blog_blogpost_change", args=[draft.pk]),
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None:
            extra_context.update(build_blog_change_form_context(request, obj))
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        old_slug = ""
        if change and obj.pk:
            old_slug = (
                BlogPost.objects.filter(pk=obj.pk)
                .values_list("slug", flat=True)
                .first()
                or ""
            )

        maybe_update_slug_from_title(obj)
        super().save_model(request, obj, form, change)

        if (
            old_slug
            and old_slug != obj.slug
            and not old_slug.startswith(DRAFT_SLUG_PREFIX)
        ):
            from apps.seo.redirects import create_redirect_for_url_change

            old_url = reverse("frontend:blog_detail", kwargs={"slug": old_slug})
            redirect = create_redirect_for_url_change(
                old_url,
                obj.get_absolute_url(),
                note=f"Automatski: promena slug-a objave „{obj.title[:100]}”",
            )
            if redirect is not None:
                messages.info(
                    request,
                    f"Kreirano 301 preusmerenje: {redirect.old_path} → {redirect.new_path}",
                )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:post_id>/page/save/",
                self.admin_site.admin_view(page_save_view),
                name="blog_blogpost_page_save",
            ),
            path(
                "page-builder/catalog/",
                self.admin_site.admin_view(page_builder_catalog_view),
                name="blog_blogpost_page_builder_catalog",
            ),
            path(
                "<int:post_id>/page/upload-image/",
                self.admin_site.admin_view(page_upload_image_view),
                name="blog_blogpost_page_upload_image",
            ),
            path(
                "<int:post_id>/page/upload-video/",
                self.admin_site.admin_view(page_upload_video_view),
                name="blog_blogpost_page_upload_video",
            ),
            path(
                "<int:post_id>/page/cleanup-pending-media/",
                self.admin_site.admin_view(page_cleanup_pending_media_view),
                name="blog_blogpost_page_cleanup_pending_media",
            ),
        ]
        return custom_urls + urls
