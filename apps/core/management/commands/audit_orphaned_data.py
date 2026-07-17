"""
Detektuje osiroćene GenericForeignKey redove i opciono osiročene medije u storage-u.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.core.orphan_audit import fix_orphaned_data, run_orphan_audit


class Command(BaseCommand):
    help = (
        "Detektuje osiroćene GenericForeignKey reference (SEO metapodaci). "
        "Koristite --fix za uklanjanje DB redova; --media-only za storage audit."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Obriši detektovane osiroćene DB redove.",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Pri --fix preskoči skeniranje/brisanje osiročenih fajlova u storage-u.",
        )
        parser.add_argument(
            "--media-only",
            action="store_true",
            help="Samo prikaži osiročene fajlove u storage-u (bez DB audita).",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Uz --media-only obriši osiročene fajlove (inače dry-run).",
        )
        parser.add_argument(
            "--minimum-age-hours",
            type=int,
            default=24,
            help="Minimum starosti fajla pre brisanja pri --media-only --confirm.",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        skip_media = options["skip_media"]
        media_only = options["media_only"]

        if media_only:
            command_args = ["cleanup_orphaned_media"]
            if options["confirm"]:
                command_args.extend(
                    [
                        "--confirm",
                        f"--minimum-age-hours={max(0, options['minimum_age_hours'])}",
                    ]
                )
            call_command(*command_args)
            return

        report = run_orphan_audit()
        self._print_report(report)

        if fix:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Primena --fix…"))
            stats = fix_orphaned_data()
            self.stdout.write(self.style.SUCCESS("Fix završen."))
            self.stdout.write(f"  Obrisano DB redova (ukupno CASCADE): {stats['db_rows_deleted']}")
            self.stdout.write(f"  Grupe nalaza:                       {stats['finding_groups']}")

            if not skip_media:
                self.stdout.write("")
                self.stdout.write("Čišćenje osiročenih medija u storage-u…")
                call_command(
                    "cleanup_orphaned_media",
                    "--confirm",
                    f"--minimum-age-hours={max(0, options['minimum_age_hours'])}",
                )

            verify = run_orphan_audit()
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
