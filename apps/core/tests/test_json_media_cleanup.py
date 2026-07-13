"""Testovi za JSON media cleanup."""

from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.test import TestCase

from apps.blog.models import BlogPost
from apps.core.json_media import (
    collect_json_media_identities,
    extract_media_refs_from_page,
)
from apps.page.structure import create_image_block, create_section


class JsonMediaCleanupTests(TestCase):
    def test_extract_media_refs_from_page_image_block(self):
        section = create_section()
        block = create_image_block()
        block["attrs"]["path"] = "blog/document/2026/07/demo.jpg"
        block["attrs"]["src"] = "/media/blog/images/blog/document/2026/07/demo.jpg"
        block["attrs"]["alt"] = "Demo"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        page = {"format": "iv_page_v1", "type": "page", "sections": [section]}

        refs = extract_media_refs_from_page(page)

        self.assertEqual(len(refs), 1)
        ref = next(iter(refs))
        self.assertEqual(ref.storage_alias, "blog_images")
        self.assertEqual(ref.path, "blog/document/2026/07/demo.jpg")

    def test_collect_json_media_identities_includes_saved_post(self):
        post = BlogPost.objects.create(
            title="Media",
            slug="media",
        )
        section = create_section()
        block = create_image_block()
        block["attrs"]["path"] = "blog/document/2026/07/post.jpg"
        block["attrs"]["alt"] = "Alt"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        page = {"format": "iv_page_v1", "type": "page", "sections": [section]}
        post.apply_body_page(page)
        post.save()

        identities = collect_json_media_identities()
        storage = storages["blog_images"]
        from apps.core.media_registry import media_identity

        expected = media_identity("blog/document/2026/07/post.jpg", storage)
        self.assertIn(expected, identities)

    def test_page_update_removes_replaced_image_file(self):
        storage = storages["blog_images"]
        path = storage.save("blog/document/2026/07/old.jpg", ContentFile(b"old", name="old.jpg"))

        post = BlogPost.objects.create(
            title="Cleanup",
            slug="cleanup",
        )
        section = create_section()
        block = create_image_block()
        block["attrs"]["path"] = path
        block["attrs"]["alt"] = "Alt"
        section["rows"][0]["columns"][0]["blocks"] = [block]
        old_page = {"format": "iv_page_v1", "type": "page", "sections": [section]}
        post.apply_body_page(old_page)
        post.save()

        new_section = create_section()
        new_block = create_image_block()
        new_block["attrs"]["alt"] = "Novo"
        new_section["rows"][0]["columns"][0]["blocks"] = [new_block]
        new_page = {"format": "iv_page_v1", "type": "page", "sections": [new_section]}

        with self.captureOnCommitCallbacks(execute=True):
            post.apply_body_page(new_page)
            post.save()

        self.assertFalse(storage.exists(path))
