from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.mixins import SeoContentMixin, TimestampMixin
from apps.page.constants import PAGE_FORMAT_V1
from apps.page.schema import page_has_content


class CMSPage(SeoContentMixin, TimestampMixin):
    """CMS stranica sa visual builder sadržajem."""

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
    body_page = models.JSONField(
        "Sadržaj (page JSON)",
        null=True,
        blank=True,
        help_text="Interni iv_page_v1 format za visual builder.",
    )
    body_plaintext = models.TextField(
        "Sadržaj (običan tekst)",
        blank=True,
        editable=False,
        help_text="Automatski izvučen iz page JSON-a za pretragu i SEO.",
    )
    body_format = models.CharField(
        "Format sadržaja",
        max_length=32,
        blank=True,
        default=PAGE_FORMAT_V1,
        help_text="Verzija internog page formata, npr. iv_page_v1.",
    )
    page_version = models.PositiveIntegerField(
        "Verzija stranice",
        default=0,
        help_text="Raste monotono pri svakoj promeni page sadržaja (čuvanje, konflikti).",
    )
    seo_metadata = GenericRelation(
        "seo.SeoMetadata",
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

    def has_page_content(self) -> bool:
        return page_has_content(self.body_page)

    def should_render_page(self) -> bool:
        return self.has_page_content()

    def apply_body_page(self, page: dict):
        from apps.page.update import apply_body_page_update

        return apply_body_page_update(self, page)

    def get_seo_context(self, request=None, *, og_type="website"):
        from apps.seo.services import build_seo_context

        return build_seo_context(self, request, og_type=og_type)


class ProjektiPage(CMSPage):
    """Proxy — admin editor za /projekti/."""

    class Meta:
        proxy = True
        verbose_name = "Stranica Projekti"
        verbose_name_plural = "Stranica Projekti"
