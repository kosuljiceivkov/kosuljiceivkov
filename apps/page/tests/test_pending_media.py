"""Testovi za parse_pending_media_items."""

from django.test import SimpleTestCase

from apps.page.pending_media import parse_pending_media_items


class ParsePendingMediaItemsTests(SimpleTestCase):
    def test_ignores_invalid_payload(self):
        self.assertEqual(parse_pending_media_items(None), [])
        self.assertEqual(parse_pending_media_items("bad"), [])

    def test_deduplicates_paths(self):
        refs = parse_pending_media_items(
            [
                {"storage": "blog_images", "path": "blog/document/2026/07/a.jpg"},
                {"storage": "blog_images", "path": "blog/document/2026/07/a.jpg"},
            ]
        )
        self.assertEqual(len(refs), 1)
