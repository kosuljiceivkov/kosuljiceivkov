"""Testovi za Projekti admin change form kontekst."""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.layout.admin_change import build_projekti_change_form_context
from apps.layout.models import CMSPage, ProjektiPage
from apps.seo.models import SeoMetadata


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

    def test_projekti_change_form_renders_og_preview_assets(self):
        user = get_user_model().objects.create_superuser(
            username="projekti-admin",
            email="projekti-admin@example.com",
            password="password",
        )
        cms_ct = ContentType.objects.get_for_model(CMSPage)
        SeoMetadata.objects.create(
            content_type=cms_ct,
            object_id=self.page.pk,
            seo_title="Projekti SEO",
        )

        self.client.force_login(user)
        response = self.client.get(
            reverse("admin:layout_projektipage_change", args=[self.page.pk])
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("seo_og_preview.js", content)
        self.assertIn("data-seo-og-preview", content)
        self.assertIn("seo-og-preview__tab", content)
        self.assertGreaterEqual(content.count("data-seo-og-preview"), 1)
