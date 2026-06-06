from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from apps.core.mixins import SeoContentMixin
from django.urls import reverse
from django.utils import timezone

from apps.core.mixins import TimestampMixin

from .querysets import BlogCategoryManager, BlogPostManager


class BlogCategory(TimestampMixin):
    """Blog kategorija sa opcionim nadkategorijama."""

    name = models.CharField("Naziv", max_length=120)
    slug = models.SlugField(
        "Slug",
        max_length=120,
        help_text="Deo URL adrese kategorije, npr. cementne-kosuljice.",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Nadkategorija",
    )
    breadcrumb_title = models.CharField(
        "Naslov u breadcrumb-u",
        max_length=100,
        blank=True,
        help_text="Prazno = naziv kategorije.",
    )
    description = models.TextField(
        "Opis",
        blank=True,
        help_text="Kratak opis za stranicu kategorije i SEO.",
    )
    is_active = models.BooleanField("Aktivna", default=True)

    objects = BlogCategoryManager()

    class Meta:
        ordering = ["name"]
        verbose_name = "Blog kategorija"
        verbose_name_plural = "Blog kategorije"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "slug"],
                name="blog_category_unique_slug_per_parent",
            ),
        ]

    def __str__(self):
        return self.name

    def get_breadcrumb_title(self) -> str:
        return self.breadcrumb_title.strip() or self.name

    def get_ancestors(self) -> list["BlogCategory"]:
        chain: list[BlogCategory] = []
        current = self.parent
        seen: set[int] = set()
        while current is not None and current.pk not in seen:
            chain.insert(0, current)
            seen.add(current.pk)
            current = current.parent
        return chain

    def get_descendant_ids(self) -> list[int]:
        ids: list[int] = []
        stack = list(self.children.filter(is_active=True).only("id"))
        while stack:
            child = stack.pop()
            ids.append(child.pk)
            stack.extend(child.children.filter(is_active=True).only("id"))
        return ids

    def get_slug_path(self) -> str:
        return "/".join(category.slug for category in self.get_ancestors() + [self])

    def get_absolute_url(self):
        return reverse(
            "frontend:blog_category",
            kwargs={"category_path": self.get_slug_path()},
        )

    def get_canonical_url(self, request=None):
        from apps.seo.canonical import build_absolute_canonical

        path = self.get_absolute_url()
        if request:
            return build_absolute_canonical(path, request)
        return path


class BlogPost(SeoContentMixin, TimestampMixin):
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
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="Kategorija",
        help_text="Koristi se za hijerarhijske breadcrumb stavke i filtriranje.",
    )
    builder_sections = GenericRelation(
        "layout.Section",
        related_query_name="blog_post",
        content_type_field="content_type",
        object_id_field="object_id",
    )
    seo_metadata = GenericRelation(
        "seo.SeoMetadata",
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

    def get_seo_context(self, request=None, *, og_type="article"):
        from apps.seo.services import build_seo_context

        return build_seo_context(self, request, og_type=og_type)
