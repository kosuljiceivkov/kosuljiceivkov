from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.page.media import EditorMediaService


class EditorMediaServiceRollbackTests(SimpleTestCase):
    def test_deletes_saved_file_when_public_url_generation_fails(self):
        storage = Mock()
        storage.url.side_effect = RuntimeError("R2 URL failure")
        service = EditorMediaService()

        with patch("apps.page.media.storages", {"project_videos": storage}):
            with self.assertRaises(RuntimeError):
                service.build_public_url_or_rollback(
                    "page/videos/2026/07/video.mp4",
                    storage_alias="project_videos",
                )

        storage.delete.assert_called_once_with("page/videos/2026/07/video.mp4")

    def test_keeps_saved_file_when_public_url_generation_succeeds(self):
        storage = Mock()
        storage.url.return_value = "https://media.example.com/video.mp4"
        service = EditorMediaService()

        with patch("apps.page.media.storages", {"project_videos": storage}):
            url = service.build_public_url_or_rollback(
                "page/videos/2026/07/video.mp4",
                storage_alias="project_videos",
            )

        self.assertEqual(url, "https://media.example.com/video.mp4")
        storage.delete.assert_not_called()
