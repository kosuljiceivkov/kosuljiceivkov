"""
Media storage backends — local filesystem (dev) and Cloudflare R2 (production).

Aliases (Django STORAGES):
  - blog_images     → image uploads (blog, Projekti, SEO, builder)
  - project_videos  → video uploads (builder)

Environment variables (R2_* preferred on Render; AWS_* legacy aliases still work):
  - R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY
  - R2_BUCKET_NAME, R2_ENDPOINT_URL, R2_CUSTOM_DOMAIN
"""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class BaseR2Storage(S3Boto3Storage):
    """Cloudflare R2 preko S3 API-ja."""

    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    region_name = settings.AWS_S3_REGION_NAME
    default_acl = None
    file_overwrite = False
    querystring_auth = False
    addressing_style = "path"
    signature_version = "s3v4"
    object_parameters = {
        "CacheControl": "public, max-age=31536000, immutable",
    }


class BlogImageR2Storage(BaseR2Storage):
    location = "images"


class ProjectVideoR2Storage(BaseR2Storage):
    location = "projects/videos"


def _local_fs(location: Path, base_url: str) -> dict:
    return {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": str(location),
            "base_url": base_url,
        },
    }


def build_local_media_storages(media_root: Path, media_url: str) -> dict:
    """STORAGES unos za lokalni razvoj."""
    media_root = Path(media_root)
    if not media_url.endswith("/"):
        media_url = f"{media_url}/"

    return {
        "default": _local_fs(media_root, media_url),
        "blog_images": _local_fs(media_root / "images", f"{media_url}images/"),
        "project_videos": _local_fs(
            media_root / "projects" / "videos",
            f"{media_url}projects/videos/",
        ),
    }


def build_r2_media_storages() -> dict:
    """STORAGES unos za produkciju (R2)."""
    return {
        "default": {"BACKEND": "config.storages.BlogImageR2Storage"},
        "blog_images": {"BACKEND": "config.storages.BlogImageR2Storage"},
        "project_videos": {"BACKEND": "config.storages.ProjectVideoR2Storage"},
    }


def get_media_url_for_r2() -> str:
    """Javni URL za medije na R2."""
    custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "") or ""
    if custom_domain:
        domain = custom_domain.strip().rstrip("/")
        if domain.startswith("http"):
            return f"{domain}/"
        return f"https://{domain}/"
    return getattr(settings, "MEDIA_URL", "/media/")
