import nested_admin
from django.contrib import admin
from django.utils.html import format_html

from apps.layout.admin_preview import render_carousel_preview, render_image_preview
from apps.layout.blocks.registry import build_block_admin_fieldsets
from apps.layout.builder_models import (
    Block,
    BlockGalleryImage,
    Carousel,
    CarouselItem,
    Column,
    Row,
    Section,
)


class BlockGalleryImageInline(nested_admin.NestedTabularInline):
    model = BlockGalleryImage
    extra = 0
    sortable_field_name = "order"
    classes = ("builder-nested-inline", "builder-nested-inline--gallery")
    fields = ("order", "image_preview", "image", "alt_text", "caption")
    readonly_fields = ("image_preview",)
    verbose_name = "Slika galerije"
    verbose_name_plural = "Slike galerije"

    @admin.display(description="Pregled")
    def image_preview(self, obj):
        return render_image_preview(obj.image)


class CarouselItemInline(nested_admin.NestedTabularInline):
    model = CarouselItem
    extra = 1
    sortable_field_name = "order"
    fields = (
        "order",
        "image_preview",
        "image",
        "alt_text",
        "title",
        "description",
        "button_text",
        "button_url",
        "button_open_new_tab",
    )
    readonly_fields = ("image_preview",)

    @admin.display(description="Pregled")
    def image_preview(self, obj):
        return render_image_preview(obj.image)


class CarouselInline(nested_admin.NestedStackedInline):
    model = Carousel
    extra = 0
    max_num = 1
    can_delete = False
    inlines = [CarouselItemInline]
    classes = ("builder-nested-inline", "builder-nested-inline--carousel")
    fields = (
        "preview",
        "autoplay",
        "show_arrows",
        "show_dots",
        "speed_ms",
        "interval_seconds",
    )
    readonly_fields = ("preview",)
    verbose_name = "Karusel"
    verbose_name_plural = "Karusel"

    class Media:
        css = {
            "all": (
                "nested_admin/dist/nested_admin.min.css",
                "admin/css/carousel_admin.css",
            ),
        }

    @admin.display(description="Pregled karusela")
    def preview(self, obj):
        return render_carousel_preview(obj)


class BlockInline(nested_admin.NestedStackedInline):
    model = Block
    extra = 0
    sortable_field_name = "order"
    classes = ("builder-inline-block",)
    inlines = [BlockGalleryImageInline, CarouselInline]
    fieldsets = build_block_admin_fieldsets()


class ColumnInline(nested_admin.NestedStackedInline):
    model = Column
    extra = 0
    sortable_field_name = "order"
    classes = ("builder-inline-column",)
    inlines = [BlockInline]
    readonly_fields = ("width_preview",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "width_preview",
                    "desktop_width",
                    "tablet_width",
                    "mobile_width",
                ),
                "classes": ("builder-column-inline",),
                "description": (
                    "Kliknite na ćelije mreže ispod da vizuelno podesite širinu "
                    "(1–12). Desktop ≥1200px · Tablet 768–1199px · Mobil ≤767px."
                ),
            },
        ),
    )

    @admin.display(description="Pregled širina")
    def width_preview(self, obj):
        return format_html(
            '<div class="builder-width-visual" data-builder-width-visual>'
            '<div class="builder-width-visual__row" data-breakpoint="desktop">'
            '<span class="builder-width-visual__label">Desktop (≥1200px)</span>'
            '<div class="builder-width-visual__track" data-width-track="desktop"></div>'
            "</div>"
            '<div class="builder-width-visual__row" data-breakpoint="tablet">'
            '<span class="builder-width-visual__label">Tablet (768–1199px)</span>'
            '<div class="builder-width-visual__track" data-width-track="tablet"></div>'
            "</div>"
            '<div class="builder-width-visual__row" data-breakpoint="mobile">'
            '<span class="builder-width-visual__label">Mobil (≤767px)</span>'
            '<div class="builder-width-visual__track" data-width-track="mobile"></div>'
            "</div>"
            "</div>"
        )


class RowInline(nested_admin.NestedStackedInline):
    model = Row
    extra = 0
    sortable_field_name = "order"
    classes = ("builder-inline-row",)
    inlines = [ColumnInline]
    fieldsets = (
        (
            None,
            {
                "fields": ("order", "gap", "vertical_align"),
                "classes": ("builder-row-inline",),
            },
        ),
    )


class SectionInline(nested_admin.NestedGenericStackedInline):
    model = Section
    extra = 0
    sortable_field_name = "order"
    classes = ("builder-inline-section",)
    inlines = [RowInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "admin_label",
                    "is_visible",
                ),
                "classes": ("builder-section-inline",),
            },
        ),
        (
            "Izgled",
            {
                "fields": (
                    "background_color",
                    "padding_top",
                    "padding_bottom",
                    "container_width",
                ),
            },
        ),
    )


class BuilderAdminMixin:
    """Ugnježdeni page builder inline za Projekti i Blog."""

    inlines = [SectionInline]

    class Media:
        css = {
            "all": (
                "nested_admin/dist/nested_admin.min.css",
                "admin/css/builder_admin.css",
            ),
        }
        js = ("admin/js/builder_admin.js",)
