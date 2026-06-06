"""Pronalaženje slika iz page buildera za SEO."""

from apps.layout.builder_models import Block
from apps.layout.builder_services import get_sections_for_object


def get_first_builder_image_field(page_object, *, visible_only=True):
    """
    Vraća prvo ImageField polje pronađeno u builder blokovima
    (slika, galerija, karusel) redosledom prikaza.
    """
    if page_object is None or not page_object.pk:
        return None

    sections = get_sections_for_object(page_object, visible_only=visible_only)
    for section in sections:
        for row in section.rows.all():
            for column in row.columns.all():
                for block in column.blocks.all():
                    image_field = _image_from_block(block)
                    if image_field is not None:
                        return image_field
    return None


def _image_from_block(block):
    if block.block_type == Block.BlockType.IMAGE and block.image:
        return block.image

    if block.block_type == Block.BlockType.GALLERY:
        for gallery_image in block.gallery_images.all():
            if gallery_image.image:
                return gallery_image.image

    if block.block_type == Block.BlockType.CAROUSEL:
        carousel = getattr(block, "carousel", None)
        if carousel is not None:
            for item in carousel.items.all():
                if item.image:
                    return item.image

    return None
