"""Kreira demo blog objavu sa Hero + CTA sekcijama za ručno testiranje."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.blog.models import BlogPost
from apps.page.tests.fixtures import sample_page


class Command(BaseCommand):
    help = "Kreira ili ažurira demo visual builder objavu (Hero + CTA) za ručni pregled."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            default="visual-builder-demo",
            help="Slug demo objave (podrazumevano: visual-builder-demo).",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Objavi demo objavu na sajtu.",
        )

    def handle(self, *args, **options):
        slug = options["slug"]
        page = sample_page()

        post, created = BlogPost.objects.get_or_create(
            slug=slug,
            defaults={
                "title": "Visual builder demo",
                "is_published": options["publish"],
                "publish_date": timezone.localdate(),
            },
        )

        post.title = "Visual builder demo"
        if options["publish"]:
            post.is_published = True
        post.apply_body_page(page)
        post.save()

        action = "Kreirana" if created else "Ažurirana"
        self.stdout.write(self.style.SUCCESS(f"{action} objava: {post.title}"))
        self.stdout.write(f"Admin: /admin/blog/blogpost/{post.pk}/change/")
        self.stdout.write(f"Javno: {post.get_absolute_url()}")
