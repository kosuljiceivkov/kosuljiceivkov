import os
from pathlib import Path, PurePosixPath

from django.apps import apps
from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import FileField
from django.utils import timezone

from apps.core.json_media import MANAGED_PREFIXES, all_media_refs


def iter_storage_files(storage_alias: str, prefix: str):
    storage = storages[storage_alias]
    try:
        directories, files = storage.listdir(prefix)
    except (FileNotFoundError, OSError):
        return
    for filename in files:
        yield str(PurePosixPath(prefix, filename))
    for directory in directories:
        yield from iter_storage_files(storage_alias, str(PurePosixPath(prefix, directory)))


def referenced_media_paths() -> set[tuple[str, str]]:
    referenced = {(ref.storage, ref.path) for ref in all_media_refs()}
    for model in apps.get_models():
        fields = [field for field in model._meta.fields if isinstance(field, FileField)]
        if not fields:
            continue
        for values in model._default_manager.values_list(
            *(field.attname for field in fields)
        ):
            if not isinstance(values, tuple):
                values = (values,)
            for field, value in zip(fields, values):
                path = str(value or "").strip()
                if not path:
                    continue
                from apps.core.json_media import _storage_alias_for_storage

                referenced.add((_storage_alias_for_storage(field.storage), path))
    return referenced


def old_enough_to_delete(storage_alias: str, path: str, minimum_age_hours: int) -> bool:
    if minimum_age_hours <= 0:
        return True
    try:
        modified = storages[storage_alias].get_modified_time(path)
    except (NotImplementedError, OSError):
        return False
    if timezone.is_naive(modified):
        modified = timezone.make_aware(modified, timezone.get_current_timezone())
    age = timezone.now() - modified
    return age.total_seconds() >= minimum_age_hours * 3600


class Command(BaseCommand):
    help = (
        "Audit managed visual-editor media and delete unreferenced files only with "
        "--confirm."
    )

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument(
            "--minimum-age-hours",
            type=int,
            default=24,
            help="Protect recent pending uploads; defaults to 24 hours.",
        )
        parser.add_argument(
            "--production-confirmation",
            default="",
            help="Required outside the local SQLite database: DELETE-ORPHANED-MEDIA.",
        )

    def handle(self, *args, **options):
        database_name = str(connection.settings_dict.get("NAME") or "")
        is_test_memory = database_name == ":memory:" or database_name.startswith(
            "file:memorydb_"
        )
        is_local_sqlite = (
            connection.vendor == "sqlite"
            and (
                is_test_memory
                or Path(database_name).resolve()
                == (settings.BASE_DIR / "db.sqlite3").resolve()
            )
        )
        if options["confirm"] and not is_local_sqlite:
            if (
                os.environ.get("R2_ORPHAN_CLEANUP_CONFIRMED") != "1"
                or options["production_confirmation"] != "DELETE-ORPHANED-MEDIA"
            ):
                raise CommandError(
                    "Production cleanup requires R2_ORPHAN_CLEANUP_CONFIRMED=1 and "
                    "--production-confirmation=DELETE-ORPHANED-MEDIA."
                )

        minimum_age_hours = max(0, options["minimum_age_hours"])
        referenced = referenced_media_paths()
        stored: set[tuple[str, str]] = set()
        for storage_alias, prefixes in MANAGED_PREFIXES.items():
            for prefix in prefixes:
                # Empty prefix = list the entire dedicated storage root.
                list_prefix = prefix.rstrip("/") if prefix else ""
                for path in iter_storage_files(storage_alias, list_prefix):
                    stored.add((storage_alias, path))

        orphaned = sorted(stored - referenced)
        deletable = [
            (storage_alias, path)
            for storage_alias, path in orphaned
            if old_enough_to_delete(storage_alias, path, minimum_age_hours)
        ]

        self.stdout.write(
            f"Managed files={len(stored)}, referenced={len(stored & referenced)}, "
            f"orphaned={len(orphaned)}, eligible_after_{minimum_age_hours}h={len(deletable)}."
        )
        for storage_alias, path in orphaned:
            self.stdout.write(f"ORPHAN [{storage_alias}] {path}")

        if not options["confirm"]:
            self.stdout.write(self.style.WARNING("DRY RUN only."))
            return

        deleted = 0
        for storage_alias, path in deletable:
            try:
                storages[storage_alias].delete(path)
                deleted += 1
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} orphaned files."))
