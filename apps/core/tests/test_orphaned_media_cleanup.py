"""Integracioni testovi za sva pravila čišćenja osiroćenih medija."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.files.storage import storages
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.blog.models import BlogPost
from apps.core.media_cleanup_service import cleanup_orphaned_media
from apps.page.structure import create_image_block, create_section, create_video_block


def _make_image(name: str = "test.jpg") -> ContentFile:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buffer, format="JPEG")
    return ContentFile(buffer.getvalue(), name=name)


class OrphanedMediaCleanupIntegrationTests(TestCase):
    def setUp(self):
        for alias in ("blog_images", "project_videos"):
            location = getattr(storages[alias], "location", None)
            if location:
                Path(location).mkdir(parents=True, exist_ok=True)

        self.user = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        self.post = BlogPost.objects.create(title="Orphan test", slug="orphan-test")
        self.image_storage = storages["blog_images"]
        self.video_storage = storages["project_videos"]

    def _page_save_url(self) -> str:
        return reverse("admin:blog_blogpost_page_save", args=[self.post.pk])

    def _cleanup_pending_url(self) -> str:
        return reverse("admin:blog_blogpost_page_cleanup_pending_media", args=[self.post.pk])

    def _page_with_image(self, path: str) -> dict:
        section = create_section()
        block = create_image_block()
        block["attrs"]["path"] = path
        block["attrs"]["alt"] = "Alt"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        return {"format": "iv_page_v1", "type": "page", "sections": [section]}

    def _page_with_video(self, path: str) -> dict:
        section = create_section()
        block = create_video_block()
        block["attrs"]["path"] = path
        block["attrs"]["src"] = f"/media/projects/videos/{path}"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        return {"format": "iv_page_v1", "type": "page", "sections": [section]}

    def test_orphan_sweep_deletes_unreferenced_files(self):
        orphan_path = self.image_storage.save(
            "blog/document/2026/07/orphan.jpg",
            ContentFile(b"orphan", name="orphan.jpg"),
        )
        self.assertTrue(self.image_storage.exists(orphan_path))

        stats = cleanup_orphaned_media(dry_run=False, storage_aliases=["blog_images"])

        self.assertGreaterEqual(stats.orphaned, 1)
        self.assertGreaterEqual(stats.deleted, 1)
        self.assertFalse(self.image_storage.exists(orphan_path))

    def test_orphan_sweep_keeps_files_referenced_in_body_page(self):
        path = self.image_storage.save(
            "blog/document/2026/07/kept.jpg",
            ContentFile(b"kept", name="kept.jpg"),
        )
        self.post.apply_body_page(self._page_with_image(path))
        self.post.save()

        stats = cleanup_orphaned_media(dry_run=False, storage_aliases=["blog_images"])

        self.assertTrue(self.image_storage.exists(path))
        self.assertEqual(stats.skipped_referenced, 0)

    def test_page_save_api_removes_replaced_image(self):
        old_path = self.image_storage.save(
            "blog/document/2026/07/old-api.jpg",
            ContentFile(b"old", name="old-api.jpg"),
        )
        old_page = self._page_with_image(old_path)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self._page_save_url(),
                data=json.dumps({"body_page": old_page, "expected_page_version": 0}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.image_storage.exists(old_path))

        new_page = {"format": "iv_page_v1", "type": "page", "sections": [create_section()]}
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self._page_save_url(),
                data=json.dumps(
                    {"body_page": new_page, "expected_page_version": response.json()["page_version"]},
                ),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.image_storage.exists(old_path))

    def test_post_delete_removes_body_page_video(self):
        video_path = self.video_storage.save(
            "page/videos/2026/07/clip.mp4",
            ContentFile(b"video-bytes", name="clip.mp4"),
        )
        self.post.apply_body_page(self._page_with_video(video_path))
        self.post.save()

        with self.captureOnCommitCallbacks(execute=True):
            self.post.delete()

        self.assertFalse(self.video_storage.exists(video_path))

    def test_pending_cleanup_deletes_abandoned_upload(self):
        path = self.image_storage.save(
            "blog/document/2026/07/abandoned.jpg",
            ContentFile(b"abandoned", name="abandoned.jpg"),
        )
        response = self.client.post(
            self._cleanup_pending_url(),
            data=json.dumps({"paths": [{"storage": "blog_images", "path": path}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertFalse(self.image_storage.exists(path))

    def test_pending_cleanup_keeps_saved_body_page_image(self):
        path = self.image_storage.save(
            "blog/document/2026/07/saved.jpg",
            ContentFile(b"saved", name="saved.jpg"),
        )
        self.post.apply_body_page(self._page_with_image(path))
        self.post.save()

        response = self.client.post(
            self._cleanup_pending_url(),
            data=json.dumps({"paths": [{"storage": "blog_images", "path": path}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["deleted"], 0)
        self.assertEqual(payload["skipped_referenced"], 1)
        self.assertTrue(self.image_storage.exists(path))

    def test_cleanup_orphaned_media_management_command(self):
        orphan_path = self.image_storage.save(
            "blog/document/2026/07/cmd-orphan.jpg",
            ContentFile(b"cmd", name="cmd-orphan.jpg"),
        )

        call_command("cleanup_orphaned_media", storages=["blog_images"])

        self.assertFalse(self.image_storage.exists(orphan_path))

    def test_featured_image_replace_removes_old_file(self):
        post = BlogPost.objects.create(title="Featured", slug="featured-replace")
        old_path = self.image_storage.save(
            "blog/featured/test/old.jpg",
            _make_image("old.jpg"),
        )
        post.featured_image = old_path
        post.save(update_fields=["featured_image"])

        new_path = self.image_storage.save(
            "blog/featured/test/new.jpg",
            _make_image("new.jpg"),
        )
        with self.captureOnCommitCallbacks(execute=True):
            post.featured_image = new_path
            post.save(update_fields=["featured_image"])

        self.assertFalse(self.image_storage.exists(old_path))
        self.assertTrue(self.image_storage.exists(new_path))
