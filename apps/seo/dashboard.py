"""SEO dashboard — agregacija problema i filtriranje sadržaja."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q

from apps.blog.models import BlogPost
from apps.layout.models import CMSPage
from apps.seo.image_seo_content import page_has_missing_alt
from apps.seo.internal_linking_content import build_site_link_graph
from apps.seo.models import SeoMetadata
from apps.seo.schema.validation import CheckStatus as SchemaCheckStatus
from apps.seo.services import (
    get_seo_fallback_description,
    get_seo_fallback_title,
    resolve_seo_title,
)

LOW_SEO_SCORE_THRESHOLD = 40
WEAK_LINKING_SCORE_THRESHOLD = 40
SCHEMA_ISSUE_SCORE_THRESHOLD = 70
DASHBOARD_PAGE_SIZE = 25


class DashboardIssue(StrEnum):
    ALL = "all"
    MISSING_TITLE = "missing_title"
    MISSING_DESCRIPTION = "missing_description"
    MISSING_SCHEMA = "missing_schema"
    MISSING_ALT = "missing_alt"
    ORPHANED = "orphaned"
    WEAK_LINKING = "weak_linking"
    LOW_SCORE = "low_score"


ISSUE_LABELS = {
    DashboardIssue.MISSING_TITLE: "Nedostaje SEO naslov",
    DashboardIssue.MISSING_DESCRIPTION: "Nedostaje meta opis",
    DashboardIssue.MISSING_SCHEMA: "Problem sa schema",
    DashboardIssue.MISSING_ALT: "Nedostaje alt tekst",
    DashboardIssue.ORPHANED: "Orphan članak",
    DashboardIssue.WEAK_LINKING: "Slabo interno linkovanje",
    DashboardIssue.LOW_SCORE: "Niska SEO ocena",
}


CONTENT_TYPE_CHOICES = (
    ("", "Svi tipovi"),
    ("blog", "Blog"),
    ("cms", "CMS stranice"),
)


@dataclass(frozen=True)
class SeoDashboardRow:
    metadata_id: int
    content_type_label: str
    content_type_id: int
    object_id: int
    title: str
    seo_title: str
    meta_description: str
    seo_score: int
    internal_linking_score: int
    image_seo_score: int
    is_cornerstone: bool
    robots_index: bool
    incoming_links: int | None
    issues: tuple[str, ...]
    edit_url: str
    seo_edit_url: str
    public_url: str

    @property
    def issue_labels(self) -> list[str]:
        return [ISSUE_LABELS.get(issue, issue) for issue in self.issues]


@dataclass
class SeoDashboardSummary:
    total: int = 0
    missing_title: int = 0
    missing_description: int = 0
    missing_schema: int = 0
    missing_alt: int = 0
    orphaned: int = 0
    weak_linking: int = 0
    low_score: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            DashboardIssue.MISSING_TITLE: self.missing_title,
            DashboardIssue.MISSING_DESCRIPTION: self.missing_description,
            DashboardIssue.MISSING_SCHEMA: self.missing_schema,
            DashboardIssue.MISSING_ALT: self.missing_alt,
            DashboardIssue.ORPHANED: self.orphaned,
            DashboardIssue.WEAK_LINKING: self.weak_linking,
            DashboardIssue.LOW_SCORE: self.low_score,
        }


@dataclass
class SeoDashboardResult:
    summary: SeoDashboardSummary
    rows: list[SeoDashboardRow]
    page_obj: object
    issue_filter: str
    content_type_filter: str
    search_query: str
    score_min: str
    score_max: str


def _blog_content_type_id() -> int:
    return ContentType.objects.get_for_model(BlogPost).pk


def _cms_content_type_id() -> int:
    return ContentType.objects.get_for_model(CMSPage).pk


def _load_content_objects(metadata_rows: list[SeoMetadata]) -> dict[tuple[int, int], object]:
    ids_by_content_type: dict[int, set[int]] = defaultdict(set)
    for row in metadata_rows:
        ids_by_content_type[row.content_type_id].add(row.object_id)

    loaded: dict[tuple[int, int], object] = {}
    blog_ct_id = _blog_content_type_id()

    for content_type_id, object_ids in ids_by_content_type.items():
        if not object_ids:
            continue

        if content_type_id == blog_ct_id:
            queryset = (
                BlogPost.objects.filter(pk__in=object_ids)
                .select_related("category")
                .prefetch_related(
                    "builder_sections__blocks__gallery_images",
                    "builder_sections__blocks__carousel__items",
                )
            )
        else:
            queryset = (
                CMSPage.objects.filter(pk__in=object_ids)
                .prefetch_related(
                    "builder_sections__blocks__gallery_images",
                    "builder_sections__blocks__carousel__items",
                )
            )

        for obj in queryset:
            loaded[(content_type_id, obj.pk)] = obj

    return loaded


def _content_type_label(content_object) -> str:
    if isinstance(content_object, BlogPost):
        return "Blog"
    if isinstance(content_object, CMSPage):
        return "CMS"
    return content_object._meta.verbose_name


def _admin_change_url(content_object) -> str:
    from django.urls import reverse

    opts = content_object._meta
    return reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[content_object.pk])


def _seo_admin_change_url(metadata_id: int) -> str:
    from django.urls import reverse

    return reverse("admin:seo_seometadata_change", args=[metadata_id])


def _public_url(content_object) -> str:
    if hasattr(content_object, "get_absolute_url"):
        try:
            return content_object.get_absolute_url() or ""
        except Exception:
            return ""
    return ""


def _has_schema_issue(content_object, metadata, request=None) -> bool:
    from apps.seo.schema.engine import preview_schema_bundle

    _, _, validation = preview_schema_bundle(
        request,
        content_object,
        metadata=metadata,
        visible_only=False,
    )
    if not validation.schema_types:
        return True
    if validation.score < SCHEMA_ISSUE_SCORE_THRESHOLD:
        return True
    return any(check.status == SchemaCheckStatus.BAD for check in validation.checks)


def _detect_issues(
    metadata: SeoMetadata,
    content_object,
    *,
    request,
    link_graph,
    blog_content_type_id: int,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not metadata.seo_title.strip():
        issues.append(DashboardIssue.MISSING_TITLE)

    if not metadata.meta_description.strip():
        issues.append(DashboardIssue.MISSING_DESCRIPTION)

    if metadata.seo_score < LOW_SEO_SCORE_THRESHOLD:
        issues.append(DashboardIssue.LOW_SCORE)

    if page_has_missing_alt(content_object, visible_only=False):
        issues.append(DashboardIssue.MISSING_ALT)

    if _has_schema_issue(content_object, metadata, request):
        issues.append(DashboardIssue.MISSING_SCHEMA)

    if metadata.content_type_id == blog_content_type_id and isinstance(content_object, BlogPost):
        incoming = len(link_graph.incoming.get(content_object.pk, set()))
        if incoming == 0:
            issues.append(DashboardIssue.ORPHANED)

        if metadata.internal_linking_score < WEAK_LINKING_SCORE_THRESHOLD:
            issues.append(DashboardIssue.WEAK_LINKING)

    return tuple(issues)


def _build_row(
    metadata: SeoMetadata,
    content_object,
    *,
    request,
    link_graph,
    blog_content_type_id: int,
) -> SeoDashboardRow:
    issues = _detect_issues(
        metadata,
        content_object,
        request=request,
        link_graph=link_graph,
        blog_content_type_id=blog_content_type_id,
    )
    incoming_links = None
    if isinstance(content_object, BlogPost):
        incoming_links = len(link_graph.incoming.get(content_object.pk, set()))

    title = resolve_seo_title(content_object, metadata) or get_seo_fallback_title(content_object)
    description = metadata.meta_description.strip() or get_seo_fallback_description(content_object)

    return SeoDashboardRow(
        metadata_id=metadata.pk,
        content_type_label=_content_type_label(content_object),
        content_type_id=metadata.content_type_id,
        object_id=metadata.object_id,
        title=title,
        seo_title=metadata.seo_title.strip() or "—",
        meta_description=description[:120] + ("…" if len(description) > 120 else ""),
        seo_score=metadata.seo_score,
        internal_linking_score=metadata.internal_linking_score,
        image_seo_score=metadata.image_seo_score,
        is_cornerstone=metadata.is_cornerstone,
        robots_index=metadata.robots_index,
        incoming_links=incoming_links,
        issues=issues,
        edit_url=_admin_change_url(content_object),
        seo_edit_url=_seo_admin_change_url(metadata.pk),
        public_url=_public_url(content_object),
    )


def _matches_content_type(content_object, content_type_filter: str) -> bool:
    if not content_type_filter:
        return True
    if content_type_filter == "blog":
        return isinstance(content_object, BlogPost)
    if content_type_filter == "cms":
        return isinstance(content_object, CMSPage)
    return True


def _matches_score(row: SeoDashboardRow, score_min: str, score_max: str) -> bool:
    if score_min:
        try:
            if row.seo_score < int(score_min):
                return False
        except ValueError:
            pass
    if score_max:
        try:
            if row.seo_score > int(score_max):
                return False
        except ValueError:
            pass
    return True


def _update_summary(summary: SeoDashboardSummary, row: SeoDashboardRow) -> None:
    summary.total += 1
    if DashboardIssue.MISSING_TITLE in row.issues:
        summary.missing_title += 1
    if DashboardIssue.MISSING_DESCRIPTION in row.issues:
        summary.missing_description += 1
    if DashboardIssue.MISSING_SCHEMA in row.issues:
        summary.missing_schema += 1
    if DashboardIssue.MISSING_ALT in row.issues:
        summary.missing_alt += 1
    if DashboardIssue.ORPHANED in row.issues:
        summary.orphaned += 1
    if DashboardIssue.WEAK_LINKING in row.issues:
        summary.weak_linking += 1
    if DashboardIssue.LOW_SCORE in row.issues:
        summary.low_score += 1


def build_seo_dashboard(
    request,
    *,
    issue_filter: str = DashboardIssue.ALL,
    content_type_filter: str = "",
    search_query: str = "",
    score_min: str = "",
    score_max: str = "",
    page: int = 1,
    page_size: int = DASHBOARD_PAGE_SIZE,
) -> SeoDashboardResult:
    metadata_qs = SeoMetadata.objects.select_related("content_type").order_by("seo_score", "-updated_at")

    if search_query.strip():
        query = search_query.strip()
        metadata_qs = metadata_qs.filter(
            Q(seo_title__icontains=query)
            | Q(meta_description__icontains=query)
            | Q(focus_keyword__icontains=query)
            | Q(secondary_keywords__icontains=query)
        )

    metadata_rows = list(metadata_qs)
    content_map = _load_content_objects(metadata_rows)
    link_graph = build_site_link_graph()
    blog_content_type_id = _blog_content_type_id()

    all_rows: list[SeoDashboardRow] = []
    summary = SeoDashboardSummary()

    for metadata in metadata_rows:
        content_object = content_map.get((metadata.content_type_id, metadata.object_id))
        if content_object is None:
            continue
        if not _matches_content_type(content_object, content_type_filter):
            continue

        row = _build_row(
            metadata,
            content_object,
            request=request,
            link_graph=link_graph,
            blog_content_type_id=blog_content_type_id,
        )
        if not _matches_score(row, score_min, score_max):
            continue

        _update_summary(summary, row)
        all_rows.append(row)

    filtered_rows = all_rows
    if issue_filter and issue_filter != DashboardIssue.ALL:
        filtered_rows = [row for row in all_rows if issue_filter in row.issues]

    paginator = Paginator(filtered_rows, page_size)
    page_obj = paginator.get_page(page)

    return SeoDashboardResult(
        summary=summary,
        rows=list(page_obj.object_list),
        page_obj=page_obj,
        issue_filter=issue_filter,
        content_type_filter=content_type_filter,
        search_query=search_query,
        score_min=score_min,
        score_max=score_max,
    )
