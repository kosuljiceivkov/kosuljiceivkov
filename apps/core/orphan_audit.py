"""
Detekcija osiroćenih GenericForeignKey redova i SEO sadržaja.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from django.contrib.contenttypes.models import ContentType
from django.db import models


@dataclass
class OrphanAuditFinding:
    category: str
    model_label: str
    pk: int
    detail: str


@dataclass
class OrphanAuditReport:
    findings: list[OrphanAuditFinding] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.findings)

    def by_category(self) -> dict[str, list[OrphanAuditFinding]]:
        grouped: dict[str, list[OrphanAuditFinding]] = {}
        for finding in self.findings:
            grouped.setdefault(finding.category, []).append(finding)
        return grouped

    def merge(self, other: OrphanAuditReport) -> None:
        self.findings.extend(other.findings)


def _target_exists(content_type: ContentType, object_id: int) -> bool:
    model_class = content_type.model_class()
    if model_class is None:
        return False
    return model_class.objects.filter(pk=object_id).exists()


def _audit_gfk_model(model: type[models.Model]) -> OrphanAuditReport:
    report = OrphanAuditReport()
    ct_field = "content_type"
    oid_field = "object_id"

    for obj in model.objects.select_related(ct_field).iterator(chunk_size=500):
        content_type = getattr(obj, ct_field, None)
        object_id = getattr(obj, oid_field, None)

        if content_type is None:
            report.findings.append(
                OrphanAuditFinding(
                    category="broken_content_type",
                    model_label=model._meta.label,
                    pk=obj.pk,
                    detail="content_type je NULL",
                )
            )
            continue

        if content_type.model_class() is None:
            report.findings.append(
                OrphanAuditFinding(
                    category="broken_content_type",
                    model_label=model._meta.label,
                    pk=obj.pk,
                    detail=f"content_type={content_type} nema model_class",
                )
            )
            continue

        if object_id is None:
            report.findings.append(
                OrphanAuditFinding(
                    category="broken_generic_reference",
                    model_label=model._meta.label,
                    pk=obj.pk,
                    detail="object_id je NULL",
                )
            )
            continue

        if not _target_exists(content_type, object_id):
            target = f"{content_type.app_label}.{content_type.model}#{object_id}"
            report.findings.append(
                OrphanAuditFinding(
                    category="broken_generic_reference",
                    model_label=model._meta.label,
                    pk=obj.pk,
                    detail=f"Cilj {target} ne postoji",
                )
            )

    return report


def audit_broken_generic_references() -> OrphanAuditReport:
    """SeoMetadata redovi čiji vlasnik ne postoji."""
    from apps.seo.models import SeoMetadata

    return _audit_gfk_model(SeoMetadata)


def audit_orphaned_media_references() -> OrphanAuditReport:
    """Medijski fajlovi na redovima sa pokvarenim GFK referencama."""
    from apps.core.media_registry import get_media_field_refs, normalize_media_name

    broken_gfk = audit_broken_generic_references()
    broken_pks: dict[str, set[int]] = {}
    for finding in broken_gfk.findings:
        if finding.category in ("broken_generic_reference", "broken_content_type"):
            broken_pks.setdefault(finding.model_label, set()).add(finding.pk)

    if not broken_pks:
        return OrphanAuditReport()

    report = OrphanAuditReport()
    for ref in get_media_field_refs():
        orphan_ids = broken_pks.get(ref.model_label)
        if not orphan_ids:
            continue
        for obj in ref.model.objects.filter(pk__in=orphan_ids).iterator(chunk_size=200):
            field_file = getattr(obj, ref.field_name, None)
            name = normalize_media_name(getattr(field_file, "name", "") or "")
            if not name:
                continue
            report.findings.append(
                OrphanAuditFinding(
                    category="orphaned_media_reference",
                    model_label=ref.model_label,
                    pk=obj.pk,
                    detail=f"{ref.field_name}={name} (vlasnik GFK osiroćen)",
                )
            )
    return report


def run_orphan_audit(*, include_media: bool = True) -> OrphanAuditReport:
    report = OrphanAuditReport()
    report.merge(audit_broken_generic_references())
    if include_media:
        report.merge(audit_orphaned_media_references())
    return report


def fix_orphaned_data(*, include_media_files: bool = True) -> dict[str, int]:
    """
    Briše detektovane osiroćene DB redove, zatim opciono osiroćene fajlove u storage-u.
    """
    from django.apps import apps as django_apps

    from apps.core.media_cleanup_service import cleanup_orphaned_media

    report = run_orphan_audit(include_media=False)
    stats: dict[str, int] = {"db_rows_deleted": 0, "finding_groups": 0}

    models_to_purge: dict[str, set[int]] = {}
    for finding in report.findings:
        models_to_purge.setdefault(finding.model_label, set()).add(finding.pk)

    for model_label, pks in models_to_purge.items():
        model = django_apps.get_model(model_label)
        deleted_count, _ = model.objects.filter(pk__in=pks).delete()
        stats["db_rows_deleted"] += deleted_count
        stats["finding_groups"] += 1

    if include_media_files:
        media_stats = cleanup_orphaned_media()
        stats["media_deleted"] = media_stats.deleted
        stats["media_orphaned"] = media_stats.orphaned
        stats["media_errors"] = media_stats.errors

    return stats
