"""Testovi za normalize_page."""

from django.test import TestCase

from apps.page.catalog import instantiate_section
from apps.page.normalize import normalize_page


class NormalizePageTests(TestCase):
    def test_legacy_template_section_becomes_rows(self):
        section = instantiate_section("hero", "classic")
        page = {"format": "iv_page_v1", "type": "page", "sections": [section]}

        normalized = normalize_page(page)

        self.assertIn("rows", normalized["sections"][0])
        self.assertNotIn("columns", normalized["sections"][0])
        self.assertEqual(len(normalized["sections"][0]["rows"]), 1)
        self.assertGreater(len(normalized["sections"][0]["rows"][0]["columns"]), 0)
