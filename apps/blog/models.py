from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.mixins import CMSMetaMixin, TimestampMixin

from .querysets import BlogPostManager


class BlogPost(CMSMetaMixin, TimestampMixin):
    """Pojedinačni blog članak."""

    title = models.CharField(
        "Naslov",
        max_length=255,
        help_text="Naslov članka — koristi se u kartici na listi bloga i u pretrazi.",
    )
    slug = models.SlugField(
        "Slug",
        max_length=255,
        unique=True,
        help_text="Deo URL adrese (npr. priprema-podloge). Generiše se iz naslova.",
    )
    excerpt = models.TextField(
        "Uvod",
        blank=True,
        help_text="Kratak tekst na kartici bloga. Prazno = koristi se meta opis.",
    )
    featured_image = models.ImageField(
        "Istaknuta slika",
        upload_to="blog/featured/%Y/%m/",
        storage="blog_images",
        blank=True,
        help_text="Prikazuje se na kartici u listi bloga. Sadržaj članka gradi se u builderu ispod.",
    )
    publish_date = models.DateField(
        "Datum objave",
        default=timezone.localdate,
        help_text="Datum prikazan posetiocima.",
    )
    is_published = models.BooleanField(
        "Objavljeno",
        default=False,
        help_text="Samo objavljene objave su vidljive na sajtu.",
    )
    builder_sections = GenericRelation(
        "layout.Section",
        related_query_name="blog_post",
        content_type_field="content_type",
        object_id_field="object_id",
    )

    objects = BlogPostManager()

    class Meta:
        ordering = ["-publish_date", "-created_at"]
        verbose_name = "Blog objava"
        verbose_name_plural = "Blog objave"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("frontend:blog_detail", kwargs={"slug": self.slug})

    def get_builder_sections(self, *, visible_only=True):
        from apps.layout.builder_services import get_sections_for_object

        return get_sections_for_object(self, visible_only=visible_only)

    def get_seo_fallback_image_url(self):
        from apps.seo.media import get_page_seo_image

        url, _, _ = get_page_seo_image(self, request=None)
        return url

    def get_seo_context(self, request=None, *, og_type="article"):
        from apps.seo.media import apply_seo_image_to_context

        context = super().get_seo_context(request, og_type=og_type)
        apply_seo_image_to_context(self, context, request)
        context["article_published_time"] = self.publish_date.isoformat()
        context["article_modified_time"] = (
            self.updated_at.isoformat() if self.updated_at else None
        )
        return context
