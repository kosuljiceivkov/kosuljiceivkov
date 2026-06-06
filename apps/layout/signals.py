from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.blog.models import BlogPost
from apps.layout.builder_cache import invalidate_builder_cache_for_host
from apps.layout.builder_models import (
    Block,
    BlockGalleryImage,
    Carousel,
    CarouselItem,
    Column,
    Row,
    Section,
)
from apps.layout.builder_services import (
    get_block_host_ids,
    get_carousel_item_host_ids,
    get_column_host_ids,
    get_gallery_image_host_ids,
    get_row_host_ids,
    get_section_host_ids,
)
from apps.layout.models import CMSPage


def _invalidate_host_ids(host_ids) -> None:
    if host_ids:
        invalidate_builder_cache_for_host(host_ids[0], host_ids[1])


@receiver(post_save, sender=Block)
def manage_carousel_for_block(sender, instance, **kwargs):
    """Kreira karusel za carousel blok; uklanja ga pri promeni tipa."""
    if instance.block_type == Block.BlockType.CAROUSEL:
        Carousel.objects.get_or_create(
            block=instance,
            defaults={
                "autoplay": True,
                "show_arrows": True,
                "show_dots": True,
                "speed_ms": 500,
                "interval_seconds": 5,
            },
        )
    else:
        Carousel.objects.filter(block=instance).delete()


@receiver(post_delete, sender=Block)
def delete_carousel_on_block_delete(sender, instance, **kwargs):
    """Uklanja karusel kada se blok obriše (za slučaj da CASCADE nije primenjen)."""
    Carousel.objects.filter(block=instance).delete()


@receiver(post_save, sender=Section)
@receiver(post_delete, sender=Section)
def invalidate_cache_on_section_change(sender, instance, **kwargs):
    _invalidate_host_ids(get_section_host_ids(instance))


@receiver(post_save, sender=Row)
@receiver(post_delete, sender=Row)
def invalidate_cache_on_row_change(sender, instance, **kwargs):
    _invalidate_host_ids(get_row_host_ids(instance))


@receiver(post_save, sender=Column)
@receiver(post_delete, sender=Column)
def invalidate_cache_on_column_change(sender, instance, **kwargs):
    _invalidate_host_ids(get_column_host_ids(instance))


@receiver(post_save, sender=Block)
@receiver(post_delete, sender=Block)
def invalidate_cache_on_block_change(sender, instance, **kwargs):
    _invalidate_host_ids(get_block_host_ids(instance))


@receiver(post_save, sender=BlockGalleryImage)
@receiver(post_delete, sender=BlockGalleryImage)
def invalidate_cache_on_gallery_image_change(sender, instance, **kwargs):
    _invalidate_host_ids(get_gallery_image_host_ids(instance))


@receiver(post_save, sender=CarouselItem)
@receiver(post_delete, sender=CarouselItem)
def invalidate_cache_on_carousel_item_change(sender, instance, **kwargs):
    _invalidate_host_ids(get_carousel_item_host_ids(instance))


@receiver(post_save, sender=Carousel)
def invalidate_cache_on_carousel_change(sender, instance, **kwargs):
    if instance.block_id:
        _invalidate_host_ids(get_block_host_ids(instance.block))


@receiver(post_save, sender=BlogPost)
@receiver(post_save, sender=CMSPage)
def invalidate_cache_on_page_host_save(sender, instance, **kwargs):
    from apps.layout.builder_cache import invalidate_builder_cache_for_page

    invalidate_builder_cache_for_page(instance)
