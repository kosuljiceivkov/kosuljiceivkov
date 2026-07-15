from django.test import SimpleTestCase

from config.settings.security import build_content_security_policy


class ContentSecurityPolicyTests(SimpleTestCase):
    def test_allows_configured_media_origin_and_youtube_frames(self):
        policy = build_content_security_policy(["https://media.example.com"])

        self.assertIn(
            "media-src 'self' https://media.example.com",
            policy,
        )
        self.assertIn(
            "frame-src https://www.youtube.com https://www.youtube-nocookie.com",
            policy,
        )
        self.assertIn(
            "img-src 'self' data: https://media.example.com",
            policy,
        )
