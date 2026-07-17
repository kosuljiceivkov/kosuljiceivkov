"""Reset development content to a clean visual-builder-only state."""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import BlogPost
from django.core.management import call_command
from apps.layout.models import CMSPage
from apps.seo.models import SeoMetadata


class Command(BaseCommand):
    help = (
        "Briše sve blog objave, resetuje Projekti page sadržaj i čisti osiročene medije. "
        "Namena: development / test okruženje."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--drop-projekti-shell",
            action="store_true",
            help="Obriši i CMS Projekti red umesto resetovanja praznog sadržaja.",
        )
        parser.add_argument(
            "--skip-media-cleanup",
            action="store_true",
            help="Ne pokreći cleanup_orphaned_media posle brisanja sadržaja.",
        )

    def handle(self, *args, **options):
        keep_projekti_shell = not options["drop_projekti_shell"]
        with transaction.atomic():
            post_ct = ContentType.objects.get_for_model(BlogPost)
            deleted_seo = SeoMetadata.objects.filter(content_type=post_ct).delete()[0]
            deleted_posts, post_details = BlogPost.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Obrisano blog objava: {deleted_posts} ({post_details})"
                )
            )
            self.stdout.write(f"Obrisano SEO metapodataka za blog: {deleted_seo}")

            page_ct = ContentType.objects.get_for_model(CMSPage)
            deleted_page_seo = SeoMetadata.objects.filter(content_type=page_ct).delete()[0]
            self.stdout.write(f"Obrisano SEO metapodataka za CMS stranice: {deleted_page_seo}")

            if keep_projekti_shell:
                page, created = CMSPage.objects.get_or_create(
                    page_type=CMSPage.PageType.PROJEKTI,
                    defaults={
                        "title": "Projekti",
                        "slug": "projekti",
                        "is_active": True,
                    },
                )
                page.title = "Projekti"
                page.slug = "projekti"
                page.is_active = True
                page.body_page = None
                page.body_plaintext = ""
                page.page_version = 0
                page.save(
                    update_fields=[
                        "title",
                        "slug",
                        "is_active",
                        "body_page",
                        "body_plaintext",
                        "page_version",
                        "updated_at",
                    ]
                )
                action = "Kreirana" if created else "Resetovana"
                self.stdout.write(self.style.SUCCESS(f"{action} prazna Projekti stranica (pk={page.pk})."))
            else:
                deleted_pages, page_details = CMSPage.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Obrisano CMS stranica: {deleted_pages} ({page_details})"
                    )
                )

        if options["skip_media_cleanup"]:
            self.stdout.write(self.style.WARNING("Preskočeno čišćenje medija."))
            return

        self.stdout.write("Ciscenje osirocenih medija...")
        call_command(
            "cleanup_orphaned_media",
            "--confirm",
            "--minimum-age-hours=0",
        )
        self.stdout.write(self.style.SUCCESS("Mediji: cleanup_orphaned_media zavrsen."))
