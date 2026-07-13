"""Testovi za čišćenje privremenih editor uploada."""

from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.test import TestCase
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.page.pending_media import cleanup_pending_editor_media, parse_pending_media_items
from apps.page.structure import create_image_block, create_section


class PendingMediaCleanupTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        self.post = BlogPost.objects.create(title="Pending", slug="pending")
        self.storage = storages["blog_images"]

    def _cleanup_url(self) -> str:
        return reverse("admin:blog_blogpost_page_cleanup_pending_media", args=[self.post.pk])

    def test_parse_pending_media_items_accepts_storage_alias(self):
        refs = parse_pending_media_items(
            [{"storage": "blog_images", "path": "blog/document/2026/07/demo.jpg"}]
        )
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].storage_alias, "blog_images")
        self.assertEqual(refs[0].path, "blog/document/2026/07/demo.jpg")

    def test_cleanup_pending_media_deletes_unreferenced_file(self):
        path = self.storage.save(
            "blog/document/2026/07/pending.jpg",
            ContentFile(b"pending", name="pending.jpg"),
        )
        refs = parse_pending_media_items([{"storage": "blog_images", "path": path}])

        stats = cleanup_pending_editor_media(refs)

        self.assertEqual(stats.deleted, 1)
        self.assertFalse(self.storage.exists(path))

    def test_cleanup_pending_media_skips_referenced_file(self):
        path = self.storage.save(
            "blog/document/2026/07/kept.jpg",
            ContentFile(b"kept", name="kept.jpg"),
        )
        section = create_section()
        block = create_image_block()
        block["attrs"]["path"] = path
        block["attrs"]["alt"] = "Alt"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        page = {"format": "iv_page_v1", "type": "page", "sections": [section]}
        self.post.apply_body_page(page)
        self.post.save()

        refs = parse_pending_media_items([{"storage": "blog_images", "path": path}])
        stats = cleanup_pending_editor_media(refs)

        self.assertEqual(stats.deleted, 0)
        self.assertEqual(stats.skipped_referenced, 1)
        self.assertTrue(self.storage.exists(path))

    def test_cleanup_pending_media_api_deletes_upload(self):
        path = self.storage.save(
            "blog/document/2026/07/api.jpg",
            ContentFile(b"api", name="api.jpg"),
        )
        response = self.client.post(
            self._cleanup_url(),
            data=json.dumps(
                {"paths": [{"storage": "blog_images", "path": path}]},
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["deleted"], 1)
        self.assertFalse(self.storage.exists(path))
