"""Testovi za CMSPage visual builder model."""

from django.test import TestCase

from apps.layout.models import CMSPage
from apps.page.tests.fixtures import sample_page


class CMSPageVisualBuilderModelTests(TestCase):
    def setUp(self):
        self.page = CMSPage.objects.create(
            title="Projekti",
            slug="projekti",
            page_type=CMSPage.PageType.PROJEKTI,
        )

    def test_page_with_content_renders(self):
        self.page.apply_body_page(sample_page())
        self.page.save()

        self.assertTrue(self.page.should_render_page())

    def test_page_without_content_does_not_render(self):
        self.assertFalse(self.page.should_render_page())
