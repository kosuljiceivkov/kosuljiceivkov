"""Dozvole za layout page admin API."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from apps.layout.models import CMSPage, ProjektiPage


def get_projekti_page_admin() -> admin.ModelAdmin:
    return admin.site._registry[ProjektiPage]


def can_edit_cms_page(request: HttpRequest, page: CMSPage) -> bool:
    model_admin = get_projekti_page_admin()
    return model_admin.has_change_permission(request, page)
