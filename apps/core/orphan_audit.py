"""
Detekcija osiroćenih GenericForeignKey redova (npr. SEO bez vlasnika).
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
    from apps.seo.models import SeoMetadata

    return _audit_gfk_model(SeoMetadata)


def run_orphan_audit() -> OrphanAuditReport:
    return audit_broken_generic_references()


def fix_orphaned_data() -> dict[str, int]:
    from django.apps import apps as django_apps

    report = run_orphan_audit()
    stats: dict[str, int] = {"db_rows_deleted": 0, "finding_groups": 0}

    models_to_purge: dict[str, set[int]] = {}
    for finding in report.findings:
        models_to_purge.setdefault(finding.model_label, set()).add(finding.pk)

    for model_label, pks in models_to_purge.items():
        model = django_apps.get_model(model_label)
        deleted_count, _ = model.objects.filter(pk__in=pks).delete()
        stats["db_rows_deleted"] += deleted_count
        stats["finding_groups"] += 1

    return stats
