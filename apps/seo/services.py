"""SEO servis — fallback vrednosti, kontekst za šablone i ocene."""

from __future__ import annotations

from typing import Any

from django.apps import apps

from apps.blog.models import BlogPost
from apps.layout.models import CMSPage
from apps.seo.constants import (
    DEFAULT_BLOG_SCHEMA,
    DEFAULT_PAGE_SCHEMA,
    SeoSchemaType,
)
from apps.seo.canonical import resolve_content_canonical
from apps.seo.content_text import get_content_plain_text
from apps.seo.helpers import resolve_absolute_url
from apps.seo.media import apply_seo_image_to_context, get_image_dimensions
from apps.seo.models import SeoMetadata
from apps.seo.robots import resolve_robots_directive
from apps.seo.scoring import ResolvedSeoScores, compute_readability_score, compute_seo_score


def get_seo_metadata(content_object) -> SeoMetadata | None:
    """Vraća SEO zapis ako postoji — ne kreira automatski."""
    if content_object is None or not getattr(content_object, "pk", None):
        return None

    prefetched = getattr(content_object, "_prefetched_objects_cache", {})
    if "seo_metadata" in prefetched:
        records = prefetched["seo_metadata"]
        return records[0] if records else None

    return (
        SeoMetadata.objects.filter(
            content_type__app_label=content_object._meta.app_label,
            content_type__model=content_object._meta.model_name,
            object_id=content_object.pk,
        )
        .select_related("content_type")
        .first()
    )


def get_default_schema_type(content_object) -> str:
    if isinstance(content_object, BlogPost):
        return DEFAULT_BLOG_SCHEMA
    if isinstance(content_object, CMSPage):
        return DEFAULT_PAGE_SCHEMA
    return SeoSchemaType.WEB_PAGE


def resolve_schema_type(content_object, metadata: SeoMetadata | None) -> str:
    from apps.seo.schema.builders import resolve_effective_schema_type

    return resolve_effective_schema_type(content_object, metadata)


def get_seo_fallback_title(content_object) -> str:
    return str(getattr(content_object, "title", "")).strip()


def get_seo_fallback_description(content_object) -> str:
    excerpt = getattr(content_object, "excerpt", "")
    if excerpt and excerpt.strip():
        return excerpt.strip()
    return get_content_plain_text(content_object)


def get_seo_fallback_canonical_path(content_object) -> str | None:
    if hasattr(content_object, "get_absolute_url"):
        url = content_object.get_absolute_url()
        if url:
            return url
    return None


def resolve_seo_title(content_object, metadata: SeoMetadata | None = None) -> str:
    metadata = metadata if metadata is not None else get_seo_metadata(content_object)
    if metadata and metadata.seo_title.strip():
        return metadata.seo_title.strip()
    return get_seo_fallback_title(content_object)


def resolve_meta_description(
    content_object,
    metadata: SeoMetadata | None = None,
) -> str:
    metadata = metadata if metadata is not None else get_seo_metadata(content_object)
    if metadata and metadata.meta_description.strip():
        return metadata.meta_description.strip()
    return get_seo_fallback_description(content_object)


def resolve_canonical_url(
    content_object,
    request=None,
    metadata: SeoMetadata | None = None,
) -> str | None:
    metadata = metadata if metadata is not None else get_seo_metadata(content_object)
    return resolve_content_canonical(content_object, request, metadata)


def resolve_breadcrumb_title(
    content_object,
    metadata: SeoMetadata | None = None,
) -> str:
    metadata = metadata if metadata is not None else get_seo_metadata(content_object)
    if metadata and metadata.breadcrumb_title.strip():
        return metadata.breadcrumb_title.strip()
    return resolve_seo_title(content_object, metadata)


def resolve_keywords(metadata: SeoMetadata | None) -> str:
    if metadata is None:
        return ""
    keywords = list(metadata.secondary_keywords_list)
    if metadata.focus_keyword.strip():
        keywords.insert(0, metadata.focus_keyword.strip())
    return ", ".join(dict.fromkeys(keywords))


def resolve_social_image_url(
    content_object,
    request,
    metadata: SeoMetadata | None,
    *,
    field_name: str,
    visible_only: bool = True,
) -> tuple[str, int | None, int | None]:
    image_field = None
    if metadata is not None:
        image_field = getattr(metadata, field_name, None)
        if image_field and getattr(image_field, "name", ""):
            url = resolve_absolute_url(request, image_field.url)
            width, height = get_image_dimensions(image_field)
            return url or "", width, height

    from apps.seo.media import get_page_seo_image

    url, width, height = get_page_seo_image(
        content_object,
        request,
        visible_only=visible_only,
    )
    return url or "", width, height


def build_seo_context(
    content_object,
    request=None,
    *,
    og_type: str = "website",
    visible_only: bool = True,
) -> dict[str, Any]:
    from apps.seo.open_graph import build_open_graph_tags

    metadata = get_seo_metadata(content_object)

    title = resolve_seo_title(content_object, metadata)
    description = resolve_meta_description(content_object, metadata)
    canonical = resolve_canonical_url(content_object, request, metadata)

    og_tags = build_open_graph_tags(
        content_object,
        request,
        metadata,
        view_og_type=og_type,
        visible_only=visible_only,
    )

    from apps.seo.twitter_card import build_twitter_card_tags

    twitter_tags = build_twitter_card_tags(
        content_object,
        request,
        metadata,
        og_tags=og_tags,
        visible_only=visible_only,
    )

    context: dict[str, Any] = {
        "title": title,
        "description": description,
        "canonical": canonical,
        "robots": resolve_robots_directive(metadata),
        "keywords": resolve_keywords(metadata),
        "focus_keyword": metadata.focus_keyword.strip() if metadata else "",
        "og_type": og_tags.og_type,
        "og_title": og_tags.og_title,
        "og_description": og_tags.og_description,
        "og_url": og_tags.og_url,
        "og_image": og_tags.og_image,
        "twitter_card": twitter_tags.twitter_card,
        "twitter_title": twitter_tags.twitter_title,
        "twitter_description": twitter_tags.twitter_description,
        "twitter_image": twitter_tags.twitter_image,
        "is_cornerstone": bool(metadata and metadata.is_cornerstone),
        "breadcrumb_title": resolve_breadcrumb_title(content_object, metadata),
        "schema_type": resolve_schema_type(content_object, metadata),
        "seo_score": metadata.seo_score if metadata else 0,
        "readability_score": metadata.readability_score if metadata else 0,
        "internal_linking_score": metadata.internal_linking_score if metadata else 0,
    }

    if og_tags.og_image_width and og_tags.og_image_height:
        context["og_image_width"] = og_tags.og_image_width
        context["og_image_height"] = og_tags.og_image_height

    if isinstance(content_object, BlogPost):
        context["article_published_time"] = content_object.publish_date.isoformat()
        context["article_modified_time"] = (
            content_object.updated_at.isoformat() if content_object.updated_at else None
        )

    if not context.get("og_image"):
        apply_seo_image_to_context(
            content_object,
            context,
            request,
            visible_only=visible_only,
        )

    return context


def refresh_seo_scores(instance: SeoMetadata) -> None:
    """Preračunava i upisuje SEO, ključnu reč i readability ocene."""
    from apps.seo.keyword_analyzer import analyze_content_object

    content_object = instance.content_object
    if content_object is None:
        instance.seo_score = 0
        instance.keyword_score = 0
        instance.readability_score = 0
        instance.internal_linking_score = 0
        instance.image_seo_score = 0
        return

    resolved = ResolvedSeoScores(
        title=resolve_seo_title(content_object, instance),
        description=resolve_meta_description(content_object, instance),
        focus_keyword=instance.focus_keyword,
        canonical=resolve_canonical_url(content_object, None, instance) or "",
        og_image=instance.og_image.url if instance.og_image else "",
        twitter_image=instance.twitter_image.url if instance.twitter_image else "",
        robots_index=instance.robots_index,
    )
    instance.seo_score = compute_seo_score(
        resolved,
        content_object=content_object,
        metadata=instance,
    )

    from apps.seo.readability_analyzer import analyze_readability_for_object

    readability_result = analyze_readability_for_object(content_object, visible_only=False)
    instance.readability_score = readability_result.score

    keyword_result = analyze_content_object(content_object, instance, visible_only=False)
    instance.keyword_score = keyword_result.score

    from apps.seo.internal_linking import analyze_internal_linking

    linking_result = analyze_internal_linking(content_object, instance, visible_only=False)
    instance.internal_linking_score = linking_result.score

    from apps.seo.image_seo import analyze_image_seo

    image_result = analyze_image_seo(content_object, instance, visible_only=False)
    instance.image_seo_score = image_result.score


SEO_SCORE_UPDATE_FIELDS = (
    "seo_score",
    "keyword_score",
    "readability_score",
    "internal_linking_score",
    "image_seo_score",
    "updated_at",
)


def persist_seo_scores_for_content(content_object) -> SeoMetadata | None:
    """
    Recompute and persist stored SEO scores for an existing SeoMetadata row.

    No-op when the content object has no SEO metadata. Score computation runs via
    the existing SeoMetadata pre_save path (refresh_seo_scores).
    """
    metadata = get_seo_metadata(content_object)
    if metadata is None:
        return None

    metadata.save(update_fields=list(SEO_SCORE_UPDATE_FIELDS))
    return metadata


def supports_seo(content_object) -> bool:
    """Proverava da li tip sadržaja podržava SEO mixin."""
    return hasattr(content_object, "get_seo_context") and hasattr(
        content_object,
        "title",
    )


def get_registered_seo_models():
    """Modeli koji koriste SeoContentMixin (blog, CMS, budući tipovi)."""
    blog_post = apps.get_model("blog", "BlogPost")
    cms_page = apps.get_model("layout", "CMSPage")
    return (blog_post, cms_page)
