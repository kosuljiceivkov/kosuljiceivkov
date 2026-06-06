"""JSON-LD structured data — generisanje i validacija."""

from __future__ import annotations

import json
from datetime import datetime, time
from typing import Any

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import BlogPost
from apps.layout.models import CMSPage

JSON_LD_CONTEXT = "https://schema.org"


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, dict):
        cleaned_dict = {}
        for key, nested in value.items():
            nested_value = _clean_value(nested)
            if nested_value is not None:
                cleaned_dict[key] = nested_value
        return cleaned_dict or None
    if isinstance(value, list):
        cleaned_list = []
        for item in value:
            nested_value = _clean_value(item)
            if nested_value is not None:
                cleaned_list.append(nested_value)
        return cleaned_list or None
    return value


def clean_schema(schema: dict[str, Any]) -> dict[str, Any] | None:
    """Uklanja prazne vrednosti i proverava obavezna polja."""
    if not schema:
        return None

    cleaned = _clean_value(schema)
    if not isinstance(cleaned, dict):
        return None
    if cleaned.get("@context") != JSON_LD_CONTEXT or not cleaned.get("@type"):
        return None
    return cleaned


def serialize_json_ld(schemas: list[dict[str, Any]]) -> list[str]:
    """
    Validira i serijalizuje JSON-LD.
    Vraća listu sigurnih JSON stringova spremnih za <script>.
    """
    serialized: list[str] = []
    for schema in schemas:
        cleaned = clean_schema(schema)
        if cleaned is None:
            continue
        try:
            json_text = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
            json.loads(json_text)
        except (TypeError, ValueError):
            continue
        json_text = json_text.replace("<", "\\u003c")
        serialized.append(json_text)
    return serialized


def _absolute(request, path_or_url: str | None) -> str | None:
    if not path_or_url:
        return None
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    if request:
        try:
            return request.build_absolute_uri(path_or_url)
        except Exception:
            pass
    base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    if base and path_or_url.startswith("/"):
        return f"{base}{path_or_url}"
    return path_or_url


def _organization_logo_url(request) -> str | None:
    logo_path = getattr(
        settings,
        "SEO_ORGANIZATION_LOGO",
        getattr(settings, "SITE_ADMIN_BRAND_LOGO", "img/logo-za-wagtail.webp"),
    )
    static_path = static(logo_path)
    return _absolute(request, static_path)


def _organization_site_url(request) -> str | None:
    configured = getattr(settings, "SITE_BASE_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    if request:
        return request.build_absolute_uri("/").rstrip("/")
    return None


def build_organization_schema(request) -> dict[str, Any] | None:
    name = getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")
    url = _organization_site_url(request)
    if not name or not url:
        return None

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "Organization",
        "name": name,
        "url": url,
    }

    logo = _organization_logo_url(request)
    if logo:
        schema["logo"] = logo

    phone = getattr(settings, "CONTACT_PHONE", "")
    if phone:
        schema["telephone"] = phone

    email = getattr(settings, "SEO_ORGANIZATION_EMAIL", "")
    if email:
        schema["email"] = email

    address = getattr(settings, "CONTACT_ADDRESS", "")
    if address:
        schema["address"] = {
            "@type": "PostalAddress",
            "addressCountry": getattr(settings, "SEO_ORGANIZATION_COUNTRY", "RS"),
            "streetAddress": address,
        }

    return clean_schema(schema)


def build_blog_posting_schema(request, post: BlogPost) -> dict[str, Any] | None:
    if not isinstance(post, BlogPost):
        return None

    headline = post.get_seo_title()
    description = post.get_seo_description()
    url = post.get_canonical_url(request)
    if not headline or not url:
        return None

    from apps.seo.media import get_page_seo_image

    image_url, _, _ = get_page_seo_image(post, request)

    published = timezone.make_aware(
        datetime.combine(post.publish_date, time.min),
        timezone.get_current_timezone(),
    )
    modified = post.updated_at or published

    author_name = getattr(
        settings,
        "SEO_BLOG_AUTHOR_NAME",
        getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov"),
    )

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "BlogPosting",
        "headline": headline,
        "description": description,
        "datePublished": published.isoformat(),
        "dateModified": modified.isoformat(),
        "author": {
            "@type": "Organization",
            "name": author_name,
        },
        "url": url,
        "mainEntityOfPage": url,
    }

    if image_url:
        schema["image"] = [image_url]

    publisher = build_organization_schema(request)
    if publisher:
        schema["publisher"] = {
            "@type": "Organization",
            "name": publisher.get("name"),
            "logo": publisher.get("logo"),
        }

    cleaned = clean_schema(schema)
    if not cleaned or not cleaned.get("headline") or not cleaned.get("url"):
        return None
    return cleaned


def build_webpage_schema(request, page: CMSPage) -> dict[str, Any] | None:
    if not isinstance(page, CMSPage):
        return None

    name = page.get_seo_title()
    description = page.get_seo_description()
    url = page.get_canonical_url(request)
    if not name or not url:
        return None

    site_name = getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")
    site_url = _organization_site_url(request)

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "WebPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": "sr-Latn",
        "isPartOf": {
            "@type": "WebSite",
            "name": site_name,
            "url": site_url,
        },
    }

    from apps.seo.media import get_page_seo_image

    image_url, _, _ = get_page_seo_image(page, request)
    if image_url:
        schema["primaryImageOfPage"] = image_url

    cleaned = clean_schema(schema)
    if not cleaned or not cleaned.get("name") or not cleaned.get("url"):
        return None
    return cleaned


def build_blog_breadcrumb_schema(request, post: BlogPost) -> dict[str, Any] | None:
    if not isinstance(post, BlogPost):
        return None

    home_url = _absolute(request, reverse("frontend:home"))
    blog_url = _absolute(request, reverse("frontend:blog"))
    article_url = post.get_canonical_url(request)
    if not home_url or not blog_url or not article_url:
        return None

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Početna",
                "item": home_url,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Blog",
                "item": blog_url,
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": post.get_seo_title(),
                "item": article_url,
            },
        ],
    }
    return clean_schema(schema)


def collect_json_ld_schemas(request, *, seo_object=None) -> list[str]:
    """Sastavlja sve validne JSON-LD šeme za trenutnu stranicu."""
    schemas: list[dict[str, Any]] = []

    organization = build_organization_schema(request)
    if organization:
        schemas.append(organization)

    if isinstance(seo_object, BlogPost):
        blog_posting = build_blog_posting_schema(request, seo_object)
        if blog_posting:
            schemas.append(blog_posting)
        breadcrumbs = build_blog_breadcrumb_schema(request, seo_object)
        if breadcrumbs:
            schemas.append(breadcrumbs)
    elif isinstance(seo_object, CMSPage) and seo_object.is_active:
        webpage = build_webpage_schema(request, seo_object)
        if webpage:
            schemas.append(webpage)

    return serialize_json_ld(schemas)
