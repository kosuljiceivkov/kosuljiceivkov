"""
Testovi životnog ciklusa podataka — brisanje, GFK cleanup, mediji, orphan audit.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management import call_command
from django.test import TestCase
from PIL import Image

from apps.blog.models import BlogPost
from apps.core.orphan_audit import run_orphan_audit
from apps.layout.models import CMSPage
from apps.page.structure import create_image_block, create_section
from apps.seo.models import SeoMetadata


def _make_image(name: str = "test.jpg") -> ContentFile:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buffer, format="JPEG")
    return ContentFile(buffer.getvalue(), name=name)


def _save_to_field(instance, field_name: str, filename: str, content: ContentFile, *, storage_alias: str) -> str:
    storage = storages[storage_alias]
    saved_name = storage.save(filename, content)
    setattr(instance, field_name, saved_name)
    instance.save(update_fields=[field_name])
    return saved_name


class DataLifecycleTests(TestCase):
    def setUp(self):
        for alias in ("blog_images", "project_videos", "default"):
            location = getattr(storages[alias], "location", None)
            if location:
                Path(location).mkdir(parents=True, exist_ok=True)

    def _delete_with_media_cleanup(self, obj):
        with self.captureOnCommitCallbacks(execute=True):
            obj.delete()

    def test_blog_post_deletion_removes_featured_image(self):
        post = BlogPost.objects.create(title="Test objava", slug="test-objava", is_published=True)
        path = _save_to_field(
            post,
            "featured_image",
            "blog/featured/test/featured.jpg",
            _make_image("featured.jpg"),
            storage_alias="blog_images",
        )
        storage = storages["blog_images"]

        self._delete_with_media_cleanup(post)

        self.assertFalse(BlogPost.objects.filter(slug="test-objava").exists())
        self.assertFalse(storage.exists(path))

    def test_blog_post_deletion_removes_json_media(self):
        storage = storages["blog_images"]
        path = storage.save("blog/document/2026/07/json.jpg", _make_image("json.jpg"))
        post = BlogPost.objects.create(
            title="JSON media",
            slug="json-media",
        )
        section = create_section()
        block = create_image_block()
        block["attrs"]["path"] = path
        block["attrs"]["alt"] = "Alt"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        page = {"format": "iv_page_v1", "type": "page", "sections": [section]}
        post.apply_body_page(page)
        post.save()

        self._delete_with_media_cleanup(post)

        self.assertFalse(storage.exists(path))

    def test_blog_post_deletion_removes_seo_rows(self):
        post = BlogPost.objects.create(title="SEO", slug="seo-post")
        SeoMetadata.objects.create(
            content_type=ContentType.objects.get_for_model(BlogPost),
            object_id=post.pk,
            focus_keyword="test",
        )

        self._delete_with_media_cleanup(post)

        self.assertFalse(SeoMetadata.objects.filter(object_id=post.pk).exists())

    def test_orphan_audit_detects_broken_generic_reference(self):
        SeoMetadata.objects.create(
            content_type=ContentType.objects.get_for_model(BlogPost),
            object_id=999999,
            focus_keyword="orphan",
        )
        report = run_orphan_audit()
        self.assertTrue(any(f.category == "broken_generic_reference" for f in report.findings))

    def test_orphan_audit_fix_removes_broken_seo_rows(self):
        SeoMetadata.objects.create(
            content_type=ContentType.objects.get_for_model(CMSPage),
            object_id=999999,
            focus_keyword="orphan",
        )
        call_command("audit_orphaned_data", "--fix", "--skip-media")
        self.assertFalse(SeoMetadata.objects.filter(object_id=999999).exists())


class StorageMediaDeletionTests(TestCase):
    def test_cleanup_pending_paths_deletes_unreferenced_file(self):
        storage = storages["blog_images"]
        path = storage.save(
            "blog/document/2026/07/demo.jpg",
            ContentFile(b"demo", name="demo.jpg"),
        )
        from apps.core.json_media import cleanup_pending_paths

        deleted = cleanup_pending_paths([{"storage": "blog_images", "path": path}])
        self.assertEqual(deleted, 1)
        self.assertFalse(storage.exists(path))
