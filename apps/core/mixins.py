from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampMixin(models.Model):
    """Zajednička polja za vreme kreiranja i izmene."""

    created_at = models.DateTimeField("Kreirano", auto_now_add=True)
    updated_at = models.DateTimeField("Ažurirano", auto_now=True)

    class Meta:
        abstract = True


class CMSMetaMixin(models.Model):
    """
    SEO meta polja za CMS modele.
    Kompatibilno sa {% render_seo_meta %} preko get_seo_context().
    """

    meta_title = models.CharField(
        "Meta naslov",
        max_length=70,
        blank=True,
        help_text=_("Preporučeno: 50–60 karaktera. Prazno = naslov stranice."),
    )
    meta_description = models.TextField(
        "Meta opis",
        blank=True,
        max_length=320,
        help_text=_("Preporučeno: 150–160 karaktera."),
    )
    canonical_url = models.URLField(
        "Kanonski URL",
        blank=True,
        help_text=_("Ostavite prazno — automatski se generiše sa javne adrese stranice."),
    )

    class Meta:
        abstract = True

    def get_seo_fallback_title(self):
        return str(getattr(self, "title", ""))

    def get_seo_fallback_description(self):
        excerpt = getattr(self, "excerpt", "")
        return excerpt.strip() if excerpt else ""

    def get_seo_title(self):
        return self.meta_title.strip() or self.get_seo_fallback_title()

    def get_seo_description(self):
        return self.meta_description.strip() or self.get_seo_fallback_description()

    def get_seo_fallback_canonical_path(self):
        if hasattr(self, "get_absolute_url"):
            url = self.get_absolute_url()
            if url:
                return url
        return None

    def get_seo_fallback_image_url(self):
        featured = getattr(self, "featured_image", None)
        if featured and getattr(featured, "url", None):
            return featured.url
        return ""

    @staticmethod
    def resolve_absolute_url(request, url):
        if not url or not request:
            return url or None
        if url.startswith(("http://", "https://")):
            return url
        return request.build_absolute_uri(url)

    def get_canonical_url(self, request):
        if self.canonical_url:
            return self.canonical_url
        path = self.get_seo_fallback_canonical_path()
        if path and request:
            return request.build_absolute_uri(path)
        return None

    def get_og_image_url(self, request):
        raw = self.get_seo_fallback_image_url()
        return self.resolve_absolute_url(request, raw)

    def get_seo_context(self, request=None, *, og_type="website"):
        title = self.get_seo_title()
        description = self.get_seo_description()
        canonical = self.get_canonical_url(request)
        og_image = self.get_og_image_url(request)

        return {
            "title": title,
            "description": description,
            "canonical": canonical,
            "robots": "index, follow",
            "keywords": "",
            "focus_keyword": "",
            "og_type": og_type,
            "og_title": title,
            "og_description": description,
            "og_image": og_image,
            "twitter_card": "summary_large_image" if og_image else "summary",
            "twitter_title": title,
            "twitter_description": description,
            "twitter_image": og_image,
        }
