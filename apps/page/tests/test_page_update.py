"""Testovi za apply_body_page_update."""

from django.test import TestCase

from apps.blog.models import BlogPost
from apps.page.tests.fixtures import sample_page
from apps.page.update import PageVersionConflictError, apply_body_page_update


class PageUpdateTests(TestCase):
    def test_apply_update_increments_page_version(self):
        post = BlogPost.objects.create(
            title="Page post",
            slug="page-post",
        )
        page = sample_page()

        result = apply_body_page_update(post, page)

        self.assertTrue(result.changed)
        self.assertEqual(result.page_version, 1)
        self.assertEqual(post.page_version, 1)
        self.assertIn("Naslov stranice", post.body_plaintext)

    def test_version_conflict_raises(self):
        post = BlogPost.objects.create(
            title="Conflict",
            slug="conflict",
        )

        with self.assertRaises(PageVersionConflictError):
            apply_body_page_update(post, sample_page(), expected_version=1)
