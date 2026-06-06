from django.db import models
from django.utils import timezone


class BlogPostQuerySet(models.QuerySet):
    """Upiti za blog objave."""

    def publicly_visible(self):
        """
        Objave vidljive na sajtu: objavljene i sa datumom objave do danas uključivo.
        """
        return self.filter(
            is_published=True,
            publish_date__lte=timezone.localdate(),
        )


class BlogPostManager(models.Manager.from_queryset(BlogPostQuerySet)):
    pass
