from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import storages
from django.db import transaction
from django.db.models import FileField
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from apps.blog.models import BlogPost
from apps.core.json_media import JsonMediaRef, all_media_refs, cleanup_deleted_page_media
from apps.layout.models import CMSPage
from apps.seo.models import SeoMetadata


def file_is_referenced(path: str, storage_alias: str = "blog_images") -> bool:
    if not path:
        return False
    ref = JsonMediaRef(storage_alias, path)
    if ref in all_media_refs():
        return True
    for model in apps.get_models():
        for field in model._meta.fields:
            if not isinstance(field, FileField):
                continue
            if model._default_manager.filter(**{field.attname: path}).exists():
                return True
    return False


def delete_later_if_unreferenced(path: str, storage_alias: str = "blog_images") -> None:
    if not path:
        return

    def cleanup():
        if not file_is_referenced(path, storage_alias):
            try:
                storages[storage_alias].delete(path)
            except Exception:
                pass

    transaction.on_commit(cleanup)


def file_name(instance, field: str) -> str:
    value = getattr(instance, field, None)
    return value.name if value else ""


@receiver(pre_save, sender=BlogPost)
def cleanup_replaced_featured_image(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = sender.objects.filter(pk=instance.pk).only("featured_image").first()
    if not old:
        return
    old_name = file_name(old, "featured_image")
    new_name = file_name(instance, "featured_image")
    if old_name and old_name != new_name:
        delete_later_if_unreferenced(old_name, "blog_images")


@receiver(post_delete, sender=BlogPost)
def cleanup_deleted_blog_post(sender, instance, **kwargs):
    delete_later_if_unreferenced(file_name(instance, "featured_image"), "blog_images")
    cleanup_deleted_page_media(instance)
    content_type = ContentType.objects.get_for_model(sender)
    SeoMetadata.objects.filter(
        content_type=content_type,
        object_id=instance.pk,
    ).delete()


@receiver(post_delete, sender=CMSPage)
def cleanup_deleted_cms_page(sender, instance, **kwargs):
    cleanup_deleted_page_media(instance)
    content_type = ContentType.objects.get_for_model(sender)
    SeoMetadata.objects.filter(
        content_type=content_type,
        object_id=instance.pk,
    ).delete()


@receiver(pre_save, sender=SeoMetadata)
def cleanup_replaced_seo_media(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = sender.objects.filter(pk=instance.pk).only("og_image", "twitter_image").first()
    if not old:
        return
    for field_name in ("og_image", "twitter_image"):
        old_name = file_name(old, field_name)
        new_name = file_name(instance, field_name)
        if old_name and old_name != new_name:
            delete_later_if_unreferenced(old_name, "blog_images")


@receiver(post_delete, sender=SeoMetadata)
def cleanup_deleted_seo_media(sender, instance, **kwargs):
    delete_later_if_unreferenced(file_name(instance, "og_image"), "blog_images")
    delete_later_if_unreferenced(file_name(instance, "twitter_image"), "blog_images")
