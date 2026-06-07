"""
Detektuje osiroćene GenericForeignKey redove, builder hijerarhiju i medije.
"""
from django.core.management.base import BaseCommand

from apps.core.media_cleanup_service import cleanup_orphaned_media
from apps.core.orphan_audit import fix_orphaned_data, run_orphan_audit


class Command(BaseCommand):
    help = (
        "Detektuje osiroćene GenericForeignKey reference, builder redove, "
        "SEO metapodatke i medijske reference. Koristite --fix za bezbedno uklanjanje."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Obriši detektovane osiroćene DB redove i osiroćene fajlove u storage-u.",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Pri --fix preskoči skeniranje/brisanje osiroćenih fajlova u storage-u.",
        )
        parser.add_argument(
            "--media-only",
            action="store_true",
            help="Samo prikaži osiroćene fajlove u storage-u (bez DB audita).",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        skip_media = options["skip_media"]
        media_only = options["media_only"]

        if media_only:
            self._report_storage_orphans(dry_run=not fix)
            return

        report = run_orphan_audit(include_media=True)
        self._print_report(report)

        if fix:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Primena --fix…"))
            stats = fix_orphaned_data(include_media_files=not skip_media)
            self.stdout.write(self.style.SUCCESS("Fix završen."))
            self.stdout.write(f"  Obrisano DB redova (ukupno CASCADE): {stats['db_rows_deleted']}")
            self.stdout.write(f"  Grupe nalaza:                       {stats['finding_groups']}")
            if not skip_media:
                self.stdout.write(f"  Obrisano medijskih fajlova:         {stats.get('media_deleted', 0)}")
                self.stdout.write(f"  Orphaned fajlova u storage:         {stats.get('media_orphaned', 0)}")
                self.stdout.write(f"  Greške pri brisanju medija:         {stats.get('media_errors', 0)}")

            verify = run_orphan_audit(include_media=False)
            if verify.total:
                self.stdout.write(
                    self.style.ERROR(
                        f"Upozorenje: {verify.total} nalaza i dalje prisutno posle --fix."
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("Verifikacija: nema preostalih DB orphan nalaza."))
        elif report.total:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"Pronađeno {report.total} nalaza. Pokrenite sa --fix za uklanjanje."
                )
            )
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Nema osiroćenih DB zapisa."))

    def _print_report(self, report) -> None:
        if not report.total:
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"Orphan audit — {report.total} nalaz(a)"))
        for category, findings in sorted(report.by_category().items()):
            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO(f"[{category}] ({len(findings)})"))
            for finding in findings[:50]:
                self.stdout.write(
                    f"  {finding.model_label} pk={finding.pk}: {finding.detail}"
                )
            if len(findings) > 50:
                self.stdout.write(f"  … i još {len(findings) - 50}")

    def _report_storage_orphans(self, *, dry_run: bool) -> None:
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — fajlovi neće biti obrisani."))
        stats = cleanup_orphaned_media(dry_run=dry_run)
        self.stdout.write(f"Referenci u bazi:     {stats.referenced_in_db}")
        self.stdout.write(f"Skenirano u storage:  {stats.scanned_storage}")
        self.stdout.write(f"Orphaned fajlova:     {stats.orphaned}")
        self.stdout.write(f"Obrisano:             {stats.deleted}")
