"""Testovi za Projekti admin change form kontekst."""

from django.test import TestCase

from apps.layout.admin_change import build_projekti_change_form_context
from apps.layout.models import CMSPage


class ProjektiAdminChangeFormTests(TestCase):
    def setUp(self):
        self.page = CMSPage.objects.create(
            title="Projekti",
            slug="projekti",
            page_type=CMSPage.PageType.PROJEKTI,
        )

    def test_build_projekti_change_form_context_includes_visual_builder_urls(self):
        context = build_projekti_change_form_context(None, self.page)

        self.assertEqual(context["blog_editor_mode"], "visual")
        self.assertIn("page/save/", context["blog_page_save_url"])
        self.assertIn("page/upload-image/", context["blog_upload_url"])
        self.assertIn("page-builder/catalog", context["blog_catalog_url"])
        self.assertEqual(context["blog_page_version"], 0)
        self.assertIn("sections", context["blog_initial_page"])
