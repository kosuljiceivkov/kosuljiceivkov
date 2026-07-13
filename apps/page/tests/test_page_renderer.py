"""Testovi za page renderer."""

from django.test import RequestFactory, TestCase

from apps.page.rendering import get_page_renderer
from apps.page.rendering.base import RenderContext
from apps.page.tests.fixtures import sample_page


class PageRendererTests(TestCase):
    def setUp(self):
        self.renderer = get_page_renderer("html")
        self.request = RequestFactory().get("/")

    def test_renders_hero_and_cta_sections(self):
        html = self.renderer.render(
            sample_page(),
            context=RenderContext(request=self.request),
        )

        self.assertIn('data-iv-page', html)
        self.assertIn("Naslov stranice", html)
        self.assertIn("Spremni za sledeći korak?", html)
        self.assertIn('data-section-id="sec_demo_hero"', html)

    def test_empty_page_renders_nothing(self):
        html = self.renderer.render({"format": "iv_page_v1", "type": "page", "sections": []})
        self.assertEqual(html, "")
