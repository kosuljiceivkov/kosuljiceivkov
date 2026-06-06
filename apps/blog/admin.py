from django.contrib import admin, messages
from django.utils.html import format_html
import nested_admin

from apps.layout.builder_page_admin import (
    BUILDER_HISTORY_FIELDSET,
    BUILDER_SECTIONS_HINT,
    BUILDER_SEO_HINT,
    BuilderHostAdminMixin,
)

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


@admin.register(BlogPost)
class BlogPostAdmin(BuilderHostAdminMixin, nested_admin.NestedModelAdmin, admin.ModelAdmin):
    list_display = ("title", "slug", "category", "publish_date", "publish_status", "updated_at")
    search_fields = ("title", "slug", "excerpt", "seo_metadata__focus_keyword")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (
        "public_url_display",
        "created_at",
        "updated_at",
    )
    actions = [publish_posts, unpublish_posts]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "public_url_display",
                    "category",
                    "excerpt",
                    "featured_image",
                ),
                "description": (
                    "Osnovne informacije za listu bloga. "
                    + BUILDER_SECTIONS_HINT
                    + " "
                    + BUILDER_SEO_HINT
                ),
            },
        ),
        (
            "Objava",
            {
                "fields": ("publish_date", "is_published"),
                "description": (
                    "Objava mora biti označena kao objavljena da bi bila vidljiva na /blog/."
                ),
            },
        ),
        BUILDER_HISTORY_FIELDSET,
    )

    @admin.display(description="Javna adresa")
    def public_url_display(self, obj):
        if obj is None or not obj.pk:
            return "— (sačuvajte objavu)"
        url = obj.get_absolute_url()
        return format_html(
            '<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>',
            url=url,
        )

    @admin.display(description="Status", boolean=True)
    def publish_status(self, obj):
        return obj.is_published
