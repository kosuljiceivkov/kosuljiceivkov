"""Testovi za YouTube URL helper."""

from django.test import TestCase

from apps.page.blocks.youtube import is_youtube_url, youtube_embed_src


class YoutubeHelperTests(TestCase):
    def test_is_youtube_url(self):
        self.assertTrue(is_youtube_url("https://www.youtube.com/watch?v=abc123"))
        self.assertTrue(is_youtube_url("https://youtu.be/abc123"))
        self.assertFalse(is_youtube_url("https://example.com/video"))

    def test_youtube_embed_src(self):
        self.assertEqual(
            youtube_embed_src("https://www.youtube.com/watch?v=abc123"),
            "https://www.youtube.com/embed/abc123",
        )
