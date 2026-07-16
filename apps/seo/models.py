"""Reusable SEO metadata — GenericForeignKey za blog, CMS i buduće tipove."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.storage_aliases import blog_images_storage
from apps.seo.constants import (
    BREADCRUMB_TITLE_MAX_LENGTH,
    KEYWORD_MAX_LENGTH,
    META_DESCRIPTION_MAX_LENGTH,
    OgType,
    RobotsMaxImagePreview,
    RobotsMaxSnippet,
    SECONDARY_KEYWORDS_MAX_LENGTH,
    SEO_TITLE_MAX_LENGTH,
    SeoSchemaType,
    TwitterCardType,
)


class SeoMetadata(models.Model):
    """
    Yoast-style SEO zapis vezan za proizvoljan sadržaj preko GFK-a.
    Sva polja su opciona — prazna vrednost koristi fallback iz sadržaja.
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tip sadržaja",
    )
    object_id = models.PositiveBigIntegerField("ID sadržaja")
    content_object = GenericForeignKey("content_type", "object_id")

    seo_title = models.CharField(
        "SEO naslov",
        max_length=SEO_TITLE_MAX_LENGTH,
        blank=True,
        help_text=_("Preporučeno: 50–60 karaktera. Prazno = naslov sadržaja."),
    )
    meta_description = models.TextField(
        "Meta opis",
        blank=True,
        max_length=META_DESCRIPTION_MAX_LENGTH,
        help_text=_("Preporučeno: 150–160 karaktera. Prazno = uvod ili tekst iz buildera."),
    )
    focus_keyword = models.CharField(
        "Fokus ključna reč",
        max_length=KEYWORD_MAX_LENGTH,
        blank=True,
        help_text=_(
            "Samo za CMS analizu i preporuke — ne izlazi u HTML meta tagove."
        ),
    )
    secondary_keywords = models.CharField(
        "Sekundarne ključne reči",
        max_length=SECONDARY_KEYWORDS_MAX_LENGTH,
        blank=True,
        help_text=_(
            "Odvojite zarezom, npr. cement, fasada, temelj. "
            "Samo za internu analizu — ne izlaze u HTML."
        ),
    )
    canonical_url = models.URLField(
        "Kanonski URL",
        blank=True,
        help_text=_(
            "Ručni override. Prazno = automatski sa javne adrese članka "
            "(bez UTM i paginacionih parametara)."
        ),
    )

    robots_index = models.BooleanField(
        "Robots: index",
        default=True,
        help_text=_("Isključite za noindex."),
    )
    robots_follow = models.BooleanField(
        "Robots: follow",
        default=True,
        help_text=_("Isključite za nofollow."),
    )
    robots_nosnippet = models.BooleanField(
        "Robots: nosnippet",
        default=False,
        help_text=_("Sprečava prikaz tekstualnog isečka u rezultatima pretrage."),
    )
    robots_noarchive = models.BooleanField(
        "Robots: noarchive",
        default=False,
        help_text=_("Sprečava link ka keširanoj verziji stranice u Google-u."),
    )
    robots_max_image_preview = models.CharField(
        "Robots: max-image-preview",
        max_length=16,
        choices=RobotsMaxImagePreview.choices,
        blank=True,
        default=RobotsMaxImagePreview.AUTO,
        help_text=_(
            "Kontroliše veličinu pregleda slike u rezultatima. "
            "Podrazumevano = bez eksplicitne direktive."
        ),
    )
    robots_max_snippet = models.CharField(
        "Robots: max-snippet",
        max_length=16,
        choices=RobotsMaxSnippet.choices,
        blank=True,
        default=RobotsMaxSnippet.AUTO,
        help_text=_(
            "Kontroliše dužinu tekstualnog isečka u rezultatima. "
            "Podrazumevano = bez eksplicitne direktive."
        ),
    )
    include_in_sitemap = models.BooleanField(
        "Uključi u sitemap",
        default=True,
        help_text=_(
            "Isključite za stranice koje ne želite u sitemap.xml "
            "(npr. thank-you, landing bez SEO vrednosti)."
        ),
    )

    og_title = models.CharField(
        "Open Graph naslov",
        max_length=SEO_TITLE_MAX_LENGTH,
        blank=True,
        help_text=_("Prazno = SEO naslov."),
    )
    og_description = models.TextField(
        "Open Graph opis",
        blank=True,
        max_length=META_DESCRIPTION_MAX_LENGTH,
        help_text=_("Prazno = meta opis."),
    )
    og_image = models.ImageField(
        "Open Graph slika",
        upload_to="seo/og/%Y/%m/",
        storage=blog_images_storage,
        blank=True,
        help_text=_(
            "Preporučeno: 1200×630 px, JPEG/PNG/WebP, max 8 MB. "
            "Prazno = istaknuta slika ili prva slika iz buildera."
        ),
    )
    og_type = models.CharField(
        "Open Graph tip",
        max_length=20,
        choices=OgType.choices,
        blank=True,
        default=OgType.AUTO,
        help_text=_("Automatski: article za blog, website za CMS stranice."),
    )
    og_url = models.URLField(
        "Open Graph URL",
        blank=True,
        help_text=_("Ručni override za og:url. Prazno = kanonski URL."),
    )

    twitter_title = models.CharField(
        "Twitter naslov",
        max_length=SEO_TITLE_MAX_LENGTH,
        blank=True,
        help_text=_("Prazno = Open Graph naslov."),
    )
    twitter_description = models.TextField(
        "Twitter opis",
        blank=True,
        max_length=META_DESCRIPTION_MAX_LENGTH,
        help_text=_("Prazno = Open Graph opis."),
    )
    twitter_image = models.ImageField(
        "Twitter slika",
        upload_to="seo/twitter/%Y/%m/",
        storage=blog_images_storage,
        blank=True,
        help_text=_(
            "Preporučeno: 1200×630 px za summary_large_image. "
            "Prazno = Open Graph slika ili istaknuta slika."
        ),
    )
    twitter_card = models.CharField(
        "Twitter Card tip",
        max_length=32,
        choices=TwitterCardType.choices,
        blank=True,
        default=TwitterCardType.AUTO,
        help_text=_(
            "Automatski: summary_large_image ako postoji slika, inače summary."
        ),
    )

    is_cornerstone = models.BooleanField(
        "Cornerstone sadržaj",
        default=False,
        help_text=_(
            "Označite glavne tematske članke. Supporting objave treba da linkuju ka njima; "
            "sistem prikazuje orphan upozorenja i preporuke klastera."
        ),
    )
    breadcrumb_title = models.CharField(
        "Naslov u breadcrumb-u",
        max_length=BREADCRUMB_TITLE_MAX_LENGTH,
        blank=True,
        help_text=_("Prazno = SEO naslov."),
    )
    schema_type = models.CharField(
        "Schema.org tip",
        max_length=32,
        choices=SeoSchemaType.choices,
        blank=True,
        default=SeoSchemaType.AUTO,
        help_text=_(
            "Primarni JSON-LD tip: BlogPosting za blog, WebPage za CMS, "
            "FAQPage ako imate FAQ u builderu, Person/Organization za profile."
        ),
    )

    seo_score = models.PositiveSmallIntegerField(
        "SEO ocena",
        default=0,
        editable=False,
    )
    keyword_score = models.PositiveSmallIntegerField(
        "Ocena ključne reči",
        default=0,
        editable=False,
    )
    readability_score = models.PositiveSmallIntegerField(
        "Ocena čitljivosti",
        default=0,
        editable=False,
    )
    internal_linking_score = models.PositiveSmallIntegerField(
        "Ocena internih linkova",
        default=0,
        editable=False,
    )
    image_seo_score = models.PositiveSmallIntegerField(
        "Ocena slika",
        default=0,
        editable=False,
    )

    updated_at = models.DateTimeField("Ažurirano", auto_now=True)

    class Meta:
        verbose_name = "SEO metapodaci"
        verbose_name_plural = "SEO metapodaci"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="seo_unique_content_object",
            ),
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        title = self.seo_title.strip() or f"#{self.object_id}"
        return f"SEO: {title}"

    def clean(self):
        from apps.seo.open_graph import validate_og_image_field_on_model
        from apps.seo.twitter_card import validate_twitter_image_field_on_model

        super().clean()
        validate_og_image_field_on_model(self)
        validate_twitter_image_field_on_model(self)

    @property
    def secondary_keywords_list(self) -> list[str]:
        if not self.secondary_keywords.strip():
            return []
        return [
            keyword.strip()
            for keyword in self.secondary_keywords.split(",")
            if keyword.strip()
        ]

