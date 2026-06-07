"""
Testovi životnog ciklusa podataka — brisanje, GFK cleanup, mediji, orphan audit.
"""
from __future__ import annotations

import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, storages
from django.core.management import call_command
from django.test import TestCase
from PIL import Image

from apps.blog.models import BlogPost
from apps.core.orphan_audit import run_orphan_audit
from apps.layout.builder_models import (
    Block,
    BlockGalleryImage,
    Carousel,
    CarouselItem,
    Column,
    Row,
    Section,
)
from apps.layout.models import CMSPage
from apps.seo.models import SeoMetadata


def _make_image(name: str = "test.jpg") -> ContentFile:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buffer, format="JPEG")
    return ContentFile(buffer.getvalue(), name=name)


def _make_video(name: str = "clip.mp4") -> ContentFile:
    return ContentFile(b"\x00\x00\x00\x20ftypmp42", name=name)


def _save_to_field(instance, field_name: str, filename: str, content: ContentFile, *, storage_alias: str) -> str:
    storage = storages[storage_alias]
    saved_name = storage.save(filename, content)
    setattr(instance, field_name, saved_name)
    instance.save(update_fields=[field_name])
    return saved_name


class BuilderFixtureMixin:
    def setUp(self):
        for alias in ("blog_images", "project_videos", "default"):
            location = getattr(storages[alias], "location", None)
            if location:
                Path(location).mkdir(parents=True, exist_ok=True)

    def _delete_with_media_cleanup(self, obj):
        with self.captureOnCommitCallbacks(execute=True):
            obj.delete()

    def _create_blog_post_with_builder(
        self,
        *,
        with_gallery: bool = False,
        with_carousel: bool = False,
        with_video: bool = False,
        featured: bool = True,
    ) -> BlogPost:
        post = BlogPost.objects.create(
            title="Test objava",
            slug="test-objava",
            is_published=True,
        )
        if featured:
            _save_to_field(
                post,
                "featured_image",
                "blog/featured/test/featured.jpg",
                _make_image("featured.jpg"),
                storage_alias="blog_images",
            )

        section = Section.objects.create(content_object=post, admin_label="Glavna")
        row = Row.objects.create(section=section)
        column = Column.objects.create(row=row)

        image_block = Block.objects.create(
            column=column,
            block_type=Block.BlockType.IMAGE,
        )
        _save_to_field(
            image_block,
            "image",
            "builder/images/test/block.jpg",
            _make_image("block.jpg"),
            storage_alias="blog_images",
        )

        if with_gallery:
            gallery_block = Block.objects.create(
                column=column,
                block_type=Block.BlockType.GALLERY,
            )
            gallery_image = BlockGalleryImage.objects.create(block=gallery_block)
            _save_to_field(
                gallery_image,
                "image",
                "builder/gallery/test/gallery.jpg",
                _make_image("gallery.jpg"),
                storage_alias="blog_images",
            )

        if with_carousel:
            carousel_block = Block.objects.create(
                column=column,
                block_type=Block.BlockType.CAROUSEL,
            )
            carousel, _ = Carousel.objects.get_or_create(block=carousel_block)
            item = CarouselItem.objects.create(carousel=carousel)
            _save_to_field(
                item,
                "image",
                "builder/carousel/test/carousel.jpg",
                _make_image("carousel.jpg"),
                storage_alias="blog_images",
            )

        if with_video:
            video_block = Block.objects.create(
                column=column,
                block_type=Block.BlockType.VIDEO,
                video_source=Block.VideoSource.FILE,
            )
            _save_to_field(
                video_block,
                "video_file",
                "builder/videos/test/clip.mp4",
                _make_video(),
                storage_alias="project_videos",
            )
            _save_to_field(
                video_block,
                "video_poster",
                "builder/posters/test/poster.jpg",
                _make_image("poster.jpg"),
                storage_alias="blog_images",
            )

        seo = SeoMetadata.objects.create(content_object=post)
        _save_to_field(
            seo,
            "og_image",
            "seo/og/test/og.jpg",
            _make_image("og.jpg"),
            storage_alias="blog_images",
        )
        _save_to_field(
            seo,
            "twitter_image",
            "seo/twitter/test/tw.jpg",
            _make_image("tw.jpg"),
            storage_alias="blog_images",
        )

        return post


class DataLifecycleTests(BuilderFixtureMixin, TestCase):
    def test_blog_post_deletion_removes_builder_and_seo_rows(self):
        post = self._create_blog_post_with_builder(
            with_gallery=True,
            with_carousel=True,
            with_video=True,
        )
        post_id = post.pk
        self._delete_with_media_cleanup(post)

        self.assertFalse(BlogPost.objects.filter(pk=post_id).exists())
        self.assertFalse(Section.objects.filter(object_id=post_id).exists())
        self.assertFalse(SeoMetadata.objects.filter(object_id=post_id).exists())
        self.assertEqual(Block.objects.count(), 0)
        self.assertEqual(BlockGalleryImage.objects.count(), 0)
        self.assertEqual(Carousel.objects.count(), 0)
        self.assertEqual(CarouselItem.objects.count(), 0)

    def test_blog_post_deletion_removes_media_files(self):
        post = self._create_blog_post_with_builder(
            with_gallery=True,
            with_carousel=True,
            with_video=True,
        )
        storage = storages["blog_images"]
        paths: set[str] = set()

        paths.add(post.featured_image.name)
        for section in post.builder_sections.prefetch_related(
            "rows__columns__blocks__gallery_images",
            "rows__columns__blocks__carousel__items",
        ):
            for row in section.rows.all():
                for column in row.columns.all():
                    for block in column.blocks.all():
                        if block.image.name:
                            paths.add(block.image.name)
                        if block.video_file.name:
                            paths.add(block.video_file.name)
                        if block.video_poster.name:
                            paths.add(block.video_poster.name)
                        for gallery_image in block.gallery_images.all():
                            paths.add(gallery_image.image.name)
                        if hasattr(block, "carousel"):
                            for item in block.carousel.items.all():
                                paths.add(item.image.name)
        for seo in post.seo_metadata.all():
            if seo.og_image.name:
                paths.add(seo.og_image.name)
            if seo.twitter_image.name:
                paths.add(seo.twitter_image.name)

        self._delete_with_media_cleanup(post)

        for path in paths:
            self.assertFalse(
                storage.exists(path),
                msg=f"Expected media removed: {path}",
            )

    def test_nested_block_deletion_cleans_media(self):
        post = self._create_blog_post_with_builder(with_gallery=False, featured=False)
        section = post.builder_sections.first()
        block = section.rows.first().columns.first().blocks.first()
        media_path = block.image.name
        storage = storages["blog_images"]

        with self.captureOnCommitCallbacks(execute=True):
            block.delete()

        self.assertFalse(Block.objects.filter(pk=block.pk).exists())
        self.assertFalse(storage.exists(media_path))

    def test_gallery_image_deletion_cleans_media(self):
        post = self._create_blog_post_with_builder(with_gallery=True, featured=False)
        gallery_block = (
            post.builder_sections.first()
            .rows.first()
            .columns.first()
            .blocks.filter(block_type=Block.BlockType.GALLERY)
            .first()
        )
        gallery_image = gallery_block.gallery_images.first()
        media_path = gallery_image.image.name
        storage = storages["blog_images"]

        with self.captureOnCommitCallbacks(execute=True):
            gallery_image.delete()

        self.assertFalse(BlockGalleryImage.objects.filter(pk=gallery_image.pk).exists())
        self.assertFalse(storage.exists(media_path))

    def test_carousel_item_deletion_cleans_media(self):
        post = self._create_blog_post_with_builder(with_carousel=True, featured=False)
        carousel_block = (
            post.builder_sections.first()
            .rows.first()
            .columns.first()
            .blocks.filter(block_type=Block.BlockType.CAROUSEL)
            .first()
        )
        item = carousel_block.carousel.items.first()
        media_path = item.image.name
        storage = storages["blog_images"]

        with self.captureOnCommitCallbacks(execute=True):
            item.delete()

        self.assertFalse(CarouselItem.objects.filter(pk=item.pk).exists())
        self.assertFalse(storage.exists(media_path))

    def test_seo_metadata_deletion_cleans_media(self):
        post = BlogPost.objects.create(title="SEO test", slug="seo-test")
        seo = SeoMetadata.objects.create(content_object=post)
        _save_to_field(
            seo,
            "og_image",
            "seo/og/test/og-only.jpg",
            _make_image(),
            storage_alias="blog_images",
        )
        og_path = seo.og_image.name
        storage = storages["blog_images"]

        with self.captureOnCommitCallbacks(execute=True):
            seo.delete()

        self.assertFalse(SeoMetadata.objects.filter(pk=seo.pk).exists())
        self.assertFalse(storage.exists(og_path))

    def test_shared_media_not_deleted_while_referenced(self):
        post_a = BlogPost.objects.create(title="A", slug="post-a")
        post_b = BlogPost.objects.create(title="B", slug="post-b")
        shared_name = _save_to_field(
            post_a,
            "featured_image",
            "blog/featured/test/shared.jpg",
            _make_image("shared.jpg"),
            storage_alias="blog_images",
        )
        post_b.featured_image = shared_name
        post_b.save(update_fields=["featured_image"])

        storage = storages["blog_images"]

        self._delete_with_media_cleanup(post_a)

        self.assertTrue(storage.exists(shared_name))
        post_b.refresh_from_db()
        self.assertEqual(post_b.featured_image.name, shared_name)

    def test_cms_page_deletion_cleans_generic_content(self):
        page = CMSPage.objects.create(title="Test CMS", slug="test-cms")
        Section.objects.create(content_object=page, admin_label="Sekcija")
        SeoMetadata.objects.create(content_object=page)
        page_id = page.pk

        page.delete()

        self.assertFalse(CMSPage.objects.filter(pk=page_id).exists())
        self.assertFalse(Section.objects.filter(object_id=page_id).exists())
        self.assertFalse(SeoMetadata.objects.filter(object_id=page_id).exists())

    def test_orphan_audit_detects_broken_generic_reference(self):
        ct = ContentType.objects.get_for_model(BlogPost)
        section = Section.objects.create(content_type=ct, object_id=999999)
        report = run_orphan_audit(include_media=False)
        categories = report.by_category()
        self.assertIn("broken_generic_reference", categories)
        self.assertTrue(any(f.pk == section.pk for f in categories["broken_generic_reference"]))

    def test_orphan_audit_fix_removes_broken_sections(self):
        ct = ContentType.objects.get_for_model(BlogPost)
        section = Section.objects.create(content_type=ct, object_id=999999)
        section_pk = section.pk

        call_command("audit_orphaned_data", "--fix", "--skip-media")
        self.assertFalse(Section.objects.filter(pk=section_pk).exists())

    def test_audit_orphaned_data_command_reports_clean_database(self):
        self._create_blog_post_with_builder()
        report_before = run_orphan_audit()
        self.assertEqual(report_before.total, 0)


class TrackingR2Storage(FileSystemStorage):
    """Simulira R2 backend — prati delete() pozive preko storage API-ja."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deleted: list[str] = []

    def delete(self, name):
        self.deleted.append(name)
        return super().delete(name)


class R2MediaDeletionTests(TestCase):
    def test_cleanup_uses_storage_delete_api(self):
        media_dir = tempfile.mkdtemp()
        try:
            storage = TrackingR2Storage(location=media_dir)
            storage.save("blog/featured/test.jpg", _make_image())

            from apps.core.media_cleanup_service import cleanup_media_file

            result = cleanup_media_file(
                "blog/featured/test.jpg",
                storage,
                reason="test_delete",
            )

            self.assertEqual(result.status, "deleted")
            self.assertIn("blog/featured/test.jpg", storage.deleted)
            self.assertFalse(storage.exists("blog/featured/test.jpg"))
        finally:
            shutil.rmtree(media_dir, ignore_errors=True)
