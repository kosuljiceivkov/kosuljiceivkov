"""
Briše medijske fajlove u R2 / lokalnom storage-u koji više nisu referencirani u bazi.
"""
from django.core.management.base import BaseCommand

from apps.core.media_cleanup_service import cleanup_orphaned_media
from apps.core.media_registry import get_media_storage_aliases


class Command(BaseCommand):
    help = (
        "Skenira FileField/ImageField reference u bazi i briše osiroćene fajlove "
        "iz Cloudflare R2 (ili lokalnog media storage-a)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Prikaži šta bi bilo obrisano, bez brisanja.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Broj osiroćenih fajlova po batch-u (podrazumevano: 100).",
        )
        parser.add_argument(
            "--storage",
            action="append",
            dest="storages",
            metavar="ALIAS",
            help=(
                "Samo navedeni storage alias (npr. blog_images). "
                "Može se ponoviti. Podrazumevano: svi media aliasi."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        storage_aliases = options["storages"]

        if batch_size < 1:
            self.stderr.write(self.style.ERROR("--batch-size mora biti >= 1."))
            return

        available = set(get_media_storage_aliases())
        if storage_aliases:
            unknown = sorted(set(storage_aliases) - available)
            if unknown:
                self.stderr.write(
                    self.style.ERROR(
                        f"Nepoznati storage aliasi: {', '.join(unknown)}. "
                        f"Dostupni: {', '.join(sorted(available))}"
                    )
                )
                return
            aliases = storage_aliases
        else:
            aliases = sorted(available)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — fajlovi nece biti obrisani."))

        self.stdout.write(f"Storage aliasi: {', '.join(aliases)}")

        stats = cleanup_orphaned_media(
            dry_run=dry_run,
            storage_aliases=aliases,
            batch_size=batch_size,
        )

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Rezultat"))
        self.stdout.write(f"  Referenci u bazi:     {stats.referenced_in_db}")
        self.stdout.write(f"  Skenirano u storage:  {stats.scanned_storage}")
        self.stdout.write(f"  Orphaned:             {stats.orphaned}")
        self.stdout.write(f"  Obrisano:             {stats.deleted}")
        self.stdout.write(f"  Preskoceno (ref):     {stats.skipped_referenced}")
        self.stdout.write(f"  Nedostaje u storage:  {stats.missing}")
        self.stdout.write(f"  Greske:               {stats.errors}")

        if dry_run and stats.orphaned:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"Pronađeno {stats.orphaned} osiroćenih fajlova. "
                    "Pokrenite bez --dry-run za brisanje."
                )
            )
        elif stats.deleted:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Ciscenje zavrseno."))
