"""Admin pogled — SEO dashboard."""

from __future__ import annotations

from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.seo.dashboard import (
    CONTENT_TYPE_CHOICES,
    ISSUE_LABELS,
    DashboardIssue,
    build_seo_dashboard,
)
from apps.seo.dashboard_actions import BULK_ACTIONS, apply_bulk_action


def seo_dashboard_view(request):
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        selected = request.POST.getlist("metadata_ids")
        metadata_ids = [int(value) for value in selected if str(value).isdigit()]
        if action and metadata_ids:
            apply_bulk_action(request, action, metadata_ids)
        return redirect(_dashboard_url(request))

    issue_filter = request.GET.get("issue", DashboardIssue.ALL)
    if issue_filter not in {item.value for item in DashboardIssue}:
        issue_filter = DashboardIssue.ALL

    content_type_filter = request.GET.get("content_type", "")
    search_query = request.GET.get("q", "")
    score_min = request.GET.get("score_min", "")
    score_max = request.GET.get("score_max", "")

    try:
        page = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page = 1

    result = build_seo_dashboard(
        request,
        issue_filter=issue_filter,
        content_type_filter=content_type_filter,
        search_query=search_query,
        score_min=score_min,
        score_max=score_max,
        page=page,
    )

    issue_cards = [
        (DashboardIssue.ALL.value, "Svi zapisi", result.summary.total),
        (DashboardIssue.MISSING_TITLE.value, ISSUE_LABELS[DashboardIssue.MISSING_TITLE], result.summary.missing_title),
        (
            DashboardIssue.MISSING_DESCRIPTION.value,
            ISSUE_LABELS[DashboardIssue.MISSING_DESCRIPTION],
            result.summary.missing_description,
        ),
        (DashboardIssue.MISSING_SCHEMA.value, ISSUE_LABELS[DashboardIssue.MISSING_SCHEMA], result.summary.missing_schema),
        (DashboardIssue.MISSING_ALT.value, ISSUE_LABELS[DashboardIssue.MISSING_ALT], result.summary.missing_alt),
        (DashboardIssue.ORPHANED.value, ISSUE_LABELS[DashboardIssue.ORPHANED], result.summary.orphaned),
        (DashboardIssue.WEAK_LINKING.value, ISSUE_LABELS[DashboardIssue.WEAK_LINKING], result.summary.weak_linking),
        (DashboardIssue.LOW_SCORE.value, ISSUE_LABELS[DashboardIssue.LOW_SCORE], result.summary.low_score),
    ]

    context = {
        **admin.site.each_context(request),
        "title": "SEO dashboard",
        "subtitle": None,
        "result": result,
        "issue_cards": issue_cards,
        "issue_filter": issue_filter,
        "content_type_choices": CONTENT_TYPE_CHOICES,
        "bulk_actions": BULK_ACTIONS,
        "issue_labels": ISSUE_LABELS,
        "opts": SeoMetadataAdminOptions(),
    }
    return render(request, "admin/seo/dashboard.html", context)


def _dashboard_url(request) -> str:
    from urllib.parse import urlencode

    source = request.POST if request.method == "POST" else request.GET
    params = {}
    for key in ("issue", "content_type", "q", "score_min", "score_max", "page"):
        value = source.get(key, "")
        if value:
            params[key] = value
    query = urlencode(params)
    base = reverse("admin:seo_dashboard")
    return f"{base}?{query}" if query else base


class SeoMetadataAdminOptions:
    """Minimalni opts objekat za admin template breadcrumbs."""

    app_label = "seo"
    model_name = "seometadata"
    verbose_name = "SEO metapodaci"
    verbose_name_plural = "SEO metapodaci"

    @property
    def app_config(self):
        from django.apps import apps

        return apps.get_app_config(self.app_label)
