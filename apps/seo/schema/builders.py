"""Schema.org builderi — Organization, Person, Article, WebPage, FAQPage, BreadcrumbList."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import BlogPost
from apps.layout.models import CMSPage
from apps.seo.constants import DEFAULT_BLOG_SCHEMA, DEFAULT_PAGE_SCHEMA, SeoSchemaType
from apps.seo.schema.base import (
    JSON_LD_CONTEXT,
    absolute_url,
    clean_schema,
    organization_logo_url,
    organization_site_url,
)
from apps.seo.schema.faq import extract_faq_items


def resolve_effective_schema_type(content_object, metadata=None) -> str:
    from apps.seo.services import get_seo_metadata

    metadata = metadata if metadata is not None else get_seo_metadata(content_object)
    if metadata and metadata.schema_type and metadata.schema_type != SeoSchemaType.AUTO:
        return metadata.schema_type

    if isinstance(content_object, BlogPost):
        return DEFAULT_BLOG_SCHEMA
    if isinstance(content_object, CMSPage):
        return DEFAULT_PAGE_SCHEMA
    return SeoSchemaType.WEB_PAGE


def build_organization_schema(request) -> dict[str, Any] | None:
    name = getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")
    url = organization_site_url(request)
    if not name or not url:
        return None

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "Organization",
        "@id": f"{url}#organization",
        "name": name,
        "url": url,
    }

    logo = organization_logo_url(request)
    if logo:
        schema["logo"] = {
            "@type": "ImageObject",
            "url": logo,
        }

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


def build_person_schema(
    request,
    *,
    name: str | None = None,
    url: str | None = None,
    image_url: str | None = None,
    job_title: str | None = None,
) -> dict[str, Any] | None:
    person_name = (
        name
        or getattr(settings, "SEO_PERSON_NAME", "")
        or getattr(settings, "SEO_BLOG_AUTHOR_NAME", "")
        or getattr(settings, "SEO_SITE_NAME", "")
    ).strip()
    if not person_name:
        return None

    person_url = url or getattr(settings, "SEO_PERSON_URL", "") or organization_site_url(request)
    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "Person",
        "name": person_name,
    }
    if person_url:
        schema["url"] = person_url
        schema["@id"] = f"{person_url}#person"

    image = image_url or getattr(settings, "SEO_PERSON_IMAGE", "")
    if image:
        schema["image"] = absolute_url(request, image)

    title = job_title or getattr(settings, "SEO_PERSON_JOB_TITLE", "")
    if title:
        schema["jobTitle"] = title

    return clean_schema(schema)


def _author_entity(request) -> dict[str, Any]:
    author_type = getattr(settings, "SEO_BLOG_AUTHOR_TYPE", "Organization").strip()
    if author_type.lower() == "person":
        person = build_person_schema(request)
        if person:
            return {
                "@type": "Person",
                "name": person.get("name"),
                "url": person.get("url"),
            }

    author_name = getattr(
        settings,
        "SEO_BLOG_AUTHOR_NAME",
        getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov"),
    )
    org = build_organization_schema(request)
    if org:
        return {
            "@type": "Organization",
            "name": author_name or org.get("name"),
            "url": org.get("url"),
        }
    return {"@type": "Organization", "name": author_name}


def build_article_schema(
    request,
    content_object,
    *,
    schema_type: str,
    metadata=None,
) -> dict[str, Any] | None:
    if not isinstance(content_object, BlogPost):
        return None

    headline = content_object.get_seo_title()
    description = content_object.get_seo_description()
    url = content_object.get_canonical_url(request)
    if not headline or not url:
        return None

    from apps.seo.media import get_page_seo_image

    image_url, _, _ = get_page_seo_image(content_object, request)
    published = timezone.make_aware(
        datetime.combine(content_object.publish_date, time.min),
        timezone.get_current_timezone(),
    )
    modified = content_object.updated_at or published

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": schema_type,
        "@id": f"{url}#{schema_type.lower()}",
        "headline": headline,
        "description": description,
        "datePublished": published.isoformat(),
        "dateModified": modified.isoformat(),
        "author": _author_entity(request),
        "url": url,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url,
        },
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

    return clean_schema(schema)


def build_webpage_schema(
    request,
    content_object,
    *,
    schema_type: str = SeoSchemaType.WEB_PAGE,
    metadata=None,
) -> dict[str, Any] | None:
    if not isinstance(content_object, CMSPage):
        return None

    name = content_object.get_seo_title()
    description = content_object.get_seo_description()
    url = content_object.get_canonical_url(request)
    if not name or not url:
        return None

    from apps.seo.media import get_page_seo_image

    site_name = getattr(settings, "SEO_SITE_NAME", "Cementne košuljice Ivkov")
    site_url = organization_site_url(request)

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": schema_type,
        "@id": f"{url}#{schema_type.lower()}",
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

    image_url, _, _ = get_page_seo_image(content_object, request)
    if image_url:
        schema["primaryImageOfPage"] = image_url

    return clean_schema(schema)


def build_faqpage_schema(
    request,
    content_object,
    *,
    metadata=None,
    visible_only: bool = True,
) -> dict[str, Any] | None:
    url = content_object.get_canonical_url(request) if hasattr(content_object, "get_canonical_url") else None
    name = content_object.get_seo_title() if hasattr(content_object, "get_seo_title") else ""
    faq_items = extract_faq_items(content_object, visible_only=visible_only)

    if not url or not faq_items:
        return None

    schema: dict[str, Any] = {
        "@context": JSON_LD_CONTEXT,
        "@type": "FAQPage",
        "@id": f"{url}#faqpage",
        "url": url,
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.answer,
                },
            }
            for item in faq_items
        ],
    }
    if name:
        schema["name"] = name

    return clean_schema(schema)


def build_breadcrumb_schema(
    request,
    content_object,
    *,
    breadcrumb_trail=None,
) -> dict[str, Any] | None:
    from apps.seo.breadcrumbs import resolve_breadcrumb_trail, trail_to_breadcrumb_schema

    trail = breadcrumb_trail or resolve_breadcrumb_trail(request, seo_object=content_object)
    page_url = None
    if content_object is not None and hasattr(content_object, "get_canonical_url"):
        page_url = content_object.get_canonical_url(request)
    return trail_to_breadcrumb_schema(request, trail, page_url=page_url)


def build_primary_schema(
    request,
    content_object,
    *,
    schema_type: str | None = None,
    metadata=None,
    visible_only: bool = True,
) -> dict[str, Any] | None:
    resolved = schema_type or resolve_effective_schema_type(content_object, metadata)

    if resolved in {SeoSchemaType.ARTICLE, SeoSchemaType.BLOG_POSTING}:
        return build_article_schema(
            request,
            content_object,
            schema_type=resolved,
            metadata=metadata,
        )

    if resolved == SeoSchemaType.FAQ_PAGE:
        return build_faqpage_schema(
            request,
            content_object,
            metadata=metadata,
            visible_only=visible_only,
        )

    if resolved == SeoSchemaType.PERSON:
        url = content_object.get_canonical_url(request) if hasattr(content_object, "get_canonical_url") else None
        from apps.seo.media import get_page_seo_image

        image_url, _, _ = get_page_seo_image(content_object, request, visible_only=visible_only)
        person = build_person_schema(request, url=url, image_url=image_url)
        if person and url:
            person["mainEntityOfPage"] = url
        return person

    if resolved == SeoSchemaType.WEB_PAGE:
        if isinstance(content_object, BlogPost):
            return build_article_schema(
                request,
                content_object,
                schema_type=SeoSchemaType.ARTICLE,
                metadata=metadata,
            )
        return build_webpage_schema(
            request,
            content_object,
            schema_type=SeoSchemaType.WEB_PAGE,
            metadata=metadata,
        )

    if resolved == SeoSchemaType.ORGANIZATION:
        return build_organization_schema(request)

    if isinstance(content_object, BlogPost):
        return build_article_schema(
            request,
            content_object,
            schema_type=SeoSchemaType.BLOG_POSTING,
            metadata=metadata,
        )

    if isinstance(content_object, CMSPage):
        return build_webpage_schema(
            request,
            content_object,
            schema_type=SeoSchemaType.WEB_PAGE,
            metadata=metadata,
        )

    return None
