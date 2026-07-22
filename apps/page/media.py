"""Upload i validacija medija za visual builder."""

from __future__ import annotations

from dataclasses import dataclass

from django.core.files.storage import storages
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
ALLOWED_VIDEO_CONTENT_TYPES = frozenset(
    {
        "video/mp4",
        "video/webm",
        "video/quicktime",
    }
)
MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_VIDEO_UPLOAD_BYTES = 200 * 1024 * 1024

# media_scope → storage location already encodes blog/ vs projects/.
# Public examples:
#   blog/images/2026/07/photo.jpg
#   blog/videos/2026/07/clip.mp4
#   projects/images/2026/07/photo.jpg
#   projects/videos/2026/07/clip.mp4
MEDIA_SCOPES = frozenset({"blog", "projects"})
IMAGE_STORAGE_BY_SCOPE = {
    "blog": "blog_images",
    "projects": "project_images",
}
VIDEO_STORAGE_BY_SCOPE = {
    "blog": "blog_videos",
    "projects": "project_videos",
}
DATE_UPLOAD_TO = "%Y/%m/"


class EditorMediaError(Exception):
    """Greška pri obradi medija u editoru."""

    def __init__(self, code: str, message: str = ""):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


@dataclass(frozen=True)
class EditorImageUploadResult:
    path: str
    url: str
    storage: str = "blog_images"
    alt: str = ""


@dataclass(frozen=True)
class EditorVideoUploadResult:
    path: str
    url: str
    storage: str = "project_videos"


class EditorMediaService:
    """Servis za upload slika i videa iz visual buildera."""

    allowed_image_content_types = ALLOWED_IMAGE_CONTENT_TYPES
    allowed_video_content_types = ALLOWED_VIDEO_CONTENT_TYPES
    max_image_upload_bytes = MAX_IMAGE_UPLOAD_BYTES
    max_video_upload_bytes = MAX_VIDEO_UPLOAD_BYTES
    image_upload_to_template = DATE_UPLOAD_TO
    video_upload_to_template = DATE_UPLOAD_TO

    def __init__(self, media_scope: str = "blog"):
        if media_scope not in MEDIA_SCOPES:
            raise ValueError(f"Unsupported media_scope: {media_scope}")
        self.media_scope = media_scope

    @property
    def image_storage_alias(self) -> str:
        return IMAGE_STORAGE_BY_SCOPE[self.media_scope]

    @property
    def video_storage_alias(self) -> str:
        return VIDEO_STORAGE_BY_SCOPE[self.media_scope]

    def validate_image(self, upload: UploadedFile) -> None:
        if upload is None:
            raise EditorMediaError("missing_image")

        if upload.size > self.max_image_upload_bytes:
            raise EditorMediaError("file_too_large")

        content_type = (upload.content_type or "").lower()
        if content_type not in self.allowed_image_content_types:
            raise EditorMediaError("invalid_content_type")

        try:
            upload.seek(0)
            with Image.open(upload) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise EditorMediaError("invalid_image") from exc
        finally:
            upload.seek(0)

    def validate_video(self, upload: UploadedFile) -> None:
        if upload is None:
            raise EditorMediaError("missing_video")

        if upload.size > self.max_video_upload_bytes:
            raise EditorMediaError("file_too_large")

        content_type = (upload.content_type or "").lower()
        if content_type not in self.allowed_video_content_types:
            raise EditorMediaError("invalid_content_type")

    def save_image(self, upload: UploadedFile) -> str:
        self.validate_image(upload)
        storage = storages[self.image_storage_alias]
        upload_prefix = timezone.now().strftime(self.image_upload_to_template)
        return storage.save(f"{upload_prefix}{upload.name}", upload)

    def save_video(self, upload: UploadedFile) -> str:
        self.validate_video(upload)
        storage = storages[self.video_storage_alias]
        upload_prefix = timezone.now().strftime(self.video_upload_to_template)
        return storage.save(f"{upload_prefix}{upload.name}", upload)

    def build_public_url(self, path: str, *, request=None, storage_alias: str = "blog_images") -> str:
        storage = storages[storage_alias]
        url = storage.url(path)
        if request is not None and url.startswith("/"):
            return request.build_absolute_uri(url)
        return url

    def build_public_url_or_rollback(
        self,
        path: str,
        *,
        request=None,
        storage_alias: str,
    ) -> str:
        """Ne ostavlja upload u storage-u ako URL ne može da se generiše."""
        try:
            return self.build_public_url(
                path,
                request=request,
                storage_alias=storage_alias,
            )
        except Exception:
            try:
                storages[storage_alias].delete(path)
            except Exception:
                pass
            raise

    def upload_image(self, upload: UploadedFile, *, request=None) -> EditorImageUploadResult:
        path = self.save_image(upload)
        alt = ""
        name = getattr(upload, "name", "") or ""
        if name:
            from pathlib import Path

            alt = Path(name).stem.replace("_", " ").replace("-", " ").strip()
        return EditorImageUploadResult(
            path=path,
            url=self.build_public_url_or_rollback(
                path,
                request=request,
                storage_alias=self.image_storage_alias,
            ),
            storage=self.image_storage_alias,
            alt=alt,
        )

    def upload_video(self, upload: UploadedFile, *, request=None) -> EditorVideoUploadResult:
        path = self.save_video(upload)
        return EditorVideoUploadResult(
            path=path,
            url=self.build_public_url_or_rollback(
                path,
                request=request,
                storage_alias=self.video_storage_alias,
            ),
            storage=self.video_storage_alias,
        )
