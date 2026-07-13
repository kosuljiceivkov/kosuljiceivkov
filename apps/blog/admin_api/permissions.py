"""Dozvole za blog document admin API."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from apps.blog.models import BlogPost


def get_blog_post_admin() -> admin.ModelAdmin:
    return admin.site._registry[BlogPost]


def can_edit_blog_post(request: HttpRequest, post: BlogPost) -> bool:
    model_admin = get_blog_post_admin()
    return model_admin.has_change_permission(request, post)
