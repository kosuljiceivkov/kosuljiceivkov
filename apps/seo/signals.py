"""SEO signal handlers — automatsko računanje ocena."""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.seo.models import SeoMetadata
from apps.seo.services import refresh_seo_scores


@receiver(pre_save, sender=SeoMetadata)
def seo_metadata_pre_save(sender, instance: SeoMetadata, **kwargs):
    refresh_seo_scores(instance)
