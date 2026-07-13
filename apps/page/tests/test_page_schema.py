"""Testovi za iv_page_v1 schema i catalog."""

from django.test import TestCase

from apps.page.catalog import instantiate_section
from apps.page.schema import empty_page, is_supported_page, page_has_content
from apps.page.tests.fixtures import sample_page
from apps.page.validation import validate_page_or_raise


class PageSchemaTests(TestCase):
    def test_empty_page_is_supported_without_content(self):
        page = empty_page()
        self.assertTrue(is_supported_page(page))
        self.assertFalse(page_has_content(page))

    def test_sample_page_has_content(self):
        page = sample_page()
        validate_page_or_raise(page)
        self.assertTrue(page_has_content(page))
        self.assertEqual(len(page["sections"]), 2)

    def test_instantiate_hero_section(self):
        section = instantiate_section("hero", "centered")
        self.assertEqual(section["template_id"], "hero")
        self.assertEqual(section["variant_id"], "centered")
        self.assertEqual(section["layout_id"], "one_full")
        self.assertEqual(len(section["columns"]), 1)
        self.assertGreaterEqual(len(section["columns"][0]["blocks"]), 3)
