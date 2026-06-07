from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch

from apps.layout.builder_models import (
    Block,
    BlockGalleryImage,
    CarouselItem,
    Column,
    Row,
    Section,
)
from apps.layout.contenttypes import get_content_type_for_model


def get_sections_for_object(page_object, *, visible_only=True):
    """
    Učitaj sekcije page buildera sa ugnježdenim strukturama za renderovanje.
    """
    if page_object is None or not page_object.pk:
        return Section.objects.none()

    content_type = get_content_type_for_model(page_object.__class__)

    blocks_qs = (
        Block.objects.select_related("carousel")
        .prefetch_related(
            Prefetch(
                "gallery_images",
                queryset=BlockGalleryImage.objects.order_by("order", "pk"),
            ),
            Prefetch(
                "carousel__items",
                queryset=CarouselItem.objects.order_by("order", "pk"),
            ),
        )
        .order_by("order", "pk")
    )

    columns_qs = Column.objects.prefetch_related(
        Prefetch("blocks", queryset=blocks_qs),
    ).order_by("order", "pk")

    rows_qs = Row.objects.prefetch_related(
        Prefetch("columns", queryset=columns_qs),
    ).order_by("order", "pk")

    queryset = (
        Section.objects.filter(
            content_type=content_type,
            object_id=page_object.pk,
        )
        .prefetch_related(Prefetch("rows", queryset=rows_qs))
        .order_by("order", "pk")
    )

    if visible_only:
        queryset = queryset.filter(is_visible=True)

    return queryset


def sections_have_carousel(sections) -> bool:
    """Provera karusela u već učitanim sekcijama — bez dodatnih upita."""
    for section in sections:
        for row in section.rows.all():
            for column in row.columns.all():
                for block in column.blocks.all():
                    if block.block_type == Block.BlockType.CAROUSEL:
                        return True
    return False


def object_has_carousel(page_object, *, visible_only=True) -> bool:
    """Brza EXISTS provera kada sekcije nisu učitane."""
    if page_object is None or not page_object.pk:
        return False

    content_type_id = get_content_type_for_model(page_object.__class__).id
    filters = {
        "block_type": Block.BlockType.CAROUSEL,
        "column__row__section__content_type_id": content_type_id,
        "column__row__section__object_id": page_object.pk,
    }
    if visible_only:
        filters["column__row__section__is_visible"] = True

    return Block.objects.filter(**filters).exists()


def get_builder_render_data(page_object, *, visible_only=True):
    """Jedan prolaz: sekcije + detekcija karusela bez dodatnog upita."""
    sections = list(get_sections_for_object(page_object, visible_only=visible_only))
    return {
        "sections": sections,
        "has_carousel": sections_have_carousel(sections),
    }


def get_section_host_ids(section) -> tuple[int, int] | None:
    if section is None or not section.content_type_id or not section.object_id:
        return None
    return section.content_type_id, section.object_id


def get_row_host_ids(row) -> tuple[int, int] | None:
    if row is None or not row.section_id:
        return None
    section_data = (
        Section.objects.filter(pk=row.section_id)
        .values("content_type_id", "object_id")
        .first()
    )
    if section_data:
        return section_data["content_type_id"], section_data["object_id"]
    return None


def get_column_host_ids(column) -> tuple[int, int] | None:
    if column is None:
        return None
    section_data = (
        Section.objects.filter(rows__columns=column)
        .values("content_type_id", "object_id")
        .first()
    )
    if section_data:
        return section_data["content_type_id"], section_data["object_id"]
    return None


def get_block_host_ids(block) -> tuple[int, int] | None:
    if block is None or not block.column_id:
        return None
    section_data = (
        Section.objects.filter(rows__columns__id=block.column_id)
        .values("content_type_id", "object_id")
        .first()
    )
    if section_data:
        return section_data["content_type_id"], section_data["object_id"]
    return None


def get_gallery_image_host_ids(gallery_image) -> tuple[int, int] | None:
    if gallery_image is None or not gallery_image.block_id:
        return None
    section_data = (
        Section.objects.filter(rows__columns__blocks__id=gallery_image.block_id)
        .values("content_type_id", "object_id")
        .first()
    )
    if section_data:
        return section_data["content_type_id"], section_data["object_id"]
    return None


def get_carousel_item_host_ids(carousel_item) -> tuple[int, int] | None:
    if carousel_item is None or not carousel_item.carousel_id:
        return None
    section_data = (
        Section.objects.filter(rows__columns__blocks__carousel__items=carousel_item)
        .values("content_type_id", "object_id")
        .first()
    )
    if section_data:
        return section_data["content_type_id"], section_data["object_id"]
    return None
