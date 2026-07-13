"""Admin forme za BlogPost visual builder."""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from apps.blog.admin_change import DRAFT_SLUG_PREFIX, DRAFT_TITLE_PLACEHOLDER
from apps.blog.models import BlogPost


class BlogPostAdminForm(forms.ModelForm):
    """Validacija objave — blokira nacrt naslov/slug."""

    class Meta:
        model = BlogPost
        fields = (
            "title",
            "slug",
            "category",
            "excerpt",
            "featured_image",
            "publish_date",
            "is_published",
        )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("is_published"):
            return cleaned_data

        title = (cleaned_data.get("title") or "").strip()
        slug = (cleaned_data.get("slug") or "").strip()

        if not title or title == DRAFT_TITLE_PLACEHOLDER:
            raise ValidationError(
                {
                    "title": (
                        "Unesite pravi naslov pre objave. "
                        "Placeholder „Bez naslova” nije dozvoljen za objavljene članke."
                    ),
                }
            )

        if slug.startswith(DRAFT_SLUG_PREFIX):
            raise ValidationError(
                {
                    "slug": (
                        "URL slug još uvek koristi privremeni nacrt prefiks. "
                        "Sačuvajte članak sa pravim naslovom da bi se slug ažurirao."
                    ),
                }
            )

        return cleaned_data
