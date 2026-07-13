"""Dual-read javni prikaz stranice Projekti."""

from django.test import TestCase
from django.urls import reverse

from apps.layout.models import CMSPage
from apps.page.tests.fixtures import sample_page


class ProjektiDualReadTests(TestCase):
    def setUp(self):
        self.page = CMSPage.objects.create(
            title="Projekti",
            slug="projekti",
            page_type=CMSPage.PageType.PROJEKTI,
            is_active=True,
        )

    def test_empty_visual_page_renders_without_legacy_builder(self):
        response = self.client.get(reverse("frontend:projekti"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-page-builder")

    def test_visual_page_renders_iv_page_content(self):
        self.page.apply_body_page(sample_page())
        self.page.save()

        response = self.client.get(reverse("frontend:projekti"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-iv-page")
        self.assertNotContains(response, "data-page-builder")
