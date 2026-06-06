from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.mixins import CMSMetaMixin, TimestampMixin


class CMSPage(CMSMetaMixin, TimestampMixin):
    """
    CMS stranica — osnova za budući page builder.
    Specijalni tipovi (npr. projekti) imaju fiksne javne rute.
    """

    class PageType(models.TextChoices):
        PROJEKTI = "projekti", "Projekti"

    title = models.CharField(
        "Naslov",
        max_length=255,
        help_text="Interni i SEO naslov stranice.",
    )
    slug = models.SlugField(
        "Slug",
        max_length=255,
        unique=True,
        help_text="Za tip „Projekti” koristite slug „projekti”.",
    )
    page_type = models.CharField(
        "Tip stranice",
        max_length=32,
        choices=PageType.choices,
        default=PageType.PROJEKTI,
        help_text='Javna stranica projekata koristi tip „Projekti” i rutu /projekti/.',
    )
    is_active = models.BooleanField(
        "Aktivna",
        default=True,
        help_text="Neaktivne stranice nisu dostupne posetiocima.",
    )
    builder_sections = GenericRelation(
        "layout.Section",
        related_query_name="cms_page",
        content_type_field="content_type",
        object_id_field="object_id",
    )

    class Meta:
        ordering = ["title"]
        verbose_name = "CMS stranica"
        verbose_name_plural = "CMS stranice"
        constraints = [
            models.UniqueConstraint(
                fields=["page_type"],
                condition=models.Q(page_type="projekti"),
                name="layout_cmspage_unique_projekti_type",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(page_type="projekti") | models.Q(slug="projekti")
                ),
                name="layout_cmspage_projekti_slug",
            ),
        ]

    def clean(self):
        super().clean()
        if self.page_type == self.PageType.PROJEKTI and self.slug != "projekti":
            raise ValidationError(
                {
                    "slug": (
                        'Za tip stranice „Projekti” slug mora biti tačno „projekti”.'
                    ),
                }
            )

    def save(self, *args, **kwargs):
        if self.page_type == self.PageType.PROJEKTI:
            self.slug = "projekti"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from apps.layout.cms_routing import get_page_public_url

        url = get_page_public_url(self)
        return url or ""

    @classmethod
    def get_projekti_page(cls):
        from apps.layout.selectors import get_projekti_page

        return get_projekti_page()

    def get_builder_sections(self, *, visible_only=True):
        from apps.layout.builder_services import get_sections_for_object

        return get_sections_for_object(self, visible_only=visible_only)

    def get_seo_fallback_image_url(self):
        from apps.seo.media import get_page_seo_image

        url, _, _ = get_page_seo_image(self, request=None)
        return url

    def get_seo_context(self, request=None, *, og_type="website"):
        from apps.seo.media import apply_seo_image_to_context

        context = super().get_seo_context(request, og_type=og_type)
        return apply_seo_image_to_context(self, context, request)


class ProjektiPage(CMSPage):
    """Proxy — admin editor za /projekti/."""

    class Meta:
        proxy = True
        verbose_name = "Stranica Projekti"
        verbose_name_plural = "Stranica Projekti"
