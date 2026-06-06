"""Plugini za postojeće tipove blokova (legacy kolone na Block modelu)."""

from django.core.exceptions import ValidationError

from apps.layout.blocks.base import AdminFieldset, BlockStorage, BlockTypePlugin
from apps.layout.builder_models import Block
from apps.layout.validators import validate_video_embed_url


def _gallery_context(block):
    prefetched = getattr(block, "_prefetched_objects_cache", {})
    if "gallery_images" in prefetched:
        return {"gallery_images": list(prefetched["gallery_images"])}
    return {"gallery_images": list(block.gallery_images.all())}


def _carousel_context(block):
    carousel = getattr(block, "carousel", None)
    if carousel is None:
        return {"carousel": None, "carousel_items": []}
    prefetched = getattr(carousel, "_prefetched_objects_cache", {})
    if "items" in prefetched:
        items = list(prefetched["items"])
    else:
        items = list(carousel.items.all())
    return {"carousel": carousel, "carousel_items": items}


def _validate_video(block):
    if (
        block.video_source == Block.VideoSource.EMBED
        and block.video_embed_url
    ):
        try:
            validate_video_embed_url(block.video_embed_url)
        except ValidationError as exc:
            raise ValidationError({"video_embed_url": exc.messages}) from exc


LEGACY_PLUGINS: tuple[BlockTypePlugin, ...] = (
    BlockTypePlugin(
        type_id="heading",
        label="Naslov",
        template="builder/blocks/heading.html",
        admin_fieldsets=(
            AdminFieldset(
                "Naslov",
                ("heading_text", "heading_level", "heading_align"),
                "builder-block-fields--heading",
            ),
        ),
    ),
    BlockTypePlugin(
        type_id="text",
        label="Tekst",
        template="builder/blocks/text.html",
        admin_fieldsets=(
            AdminFieldset(
                "Tekst",
                ("text_content", "text_align"),
                "builder-block-fields--text",
            ),
        ),
    ),
    BlockTypePlugin(
        type_id="image",
        label="Slika",
        template="builder/blocks/image.html",
        admin_fieldsets=(
            AdminFieldset(
                "Slika",
                ("image", "image_alt", "image_caption", "image_link_url"),
                "builder-block-fields--image",
            ),
        ),
    ),
    BlockTypePlugin(
        type_id="button",
        label="Dugme",
        template="builder/blocks/button.html",
        admin_fieldsets=(
            AdminFieldset(
                "Dugme",
                (
                    "button_label",
                    "button_url",
                    "button_style",
                    "button_open_new_tab",
                ),
                "builder-block-fields--button",
            ),
        ),
    ),
    BlockTypePlugin(
        type_id="video",
        label="Video",
        template="builder/blocks/video.html",
        admin_fieldsets=(
            AdminFieldset(
                "Video",
                (
                    "video_source",
                    "video_embed_url",
                    "video_file",
                    "video_poster",
                ),
                "builder-block-fields--video",
            ),
        ),
        validate=_validate_video,
    ),
    BlockTypePlugin(
        type_id="spacer",
        label="Razmak",
        template="builder/blocks/spacer.html",
        admin_fieldsets=(
            AdminFieldset(
                "Razmak",
                ("spacer_height", "spacer_height_mobile"),
                "builder-block-fields--spacer",
            ),
        ),
    ),
    BlockTypePlugin(
        type_id="divider",
        label="Linija",
        template="builder/blocks/divider.html",
        admin_fieldsets=(
            AdminFieldset(
                "Linija",
                ("divider_style", "divider_width"),
                "builder-block-fields--divider",
            ),
        ),
    ),
    BlockTypePlugin(
        type_id="gallery",
        label="Galerija",
        template="builder/blocks/gallery.html",
        needs_gallery=True,
        get_context=_gallery_context,
        admin_fieldsets=(),
    ),
    BlockTypePlugin(
        type_id="carousel",
        label="Karusel",
        template="builder/blocks/carousel/index.html",
        needs_carousel=True,
        get_context=_carousel_context,
        admin_fieldsets=(),
    ),
)
