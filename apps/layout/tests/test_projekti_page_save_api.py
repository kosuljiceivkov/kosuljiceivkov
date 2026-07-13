"""Testovi za Projekti page save API."""

from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.layout.models import CMSPage
from apps.page.tests.fixtures import sample_page


class ProjektiPageSaveApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        self.page = CMSPage.objects.create(
            title="Projekti",
            slug="projekti",
            page_type=CMSPage.PageType.PROJEKTI,
        )

    def _page_save_url(self) -> str:
        return reverse("admin:layout_projektipage_page_save", args=[self.page.pk])

    def test_page_save_persists_page(self):
        page = sample_page()
        response = self.client.post(
            self._page_save_url(),
            data=json.dumps({"body_page": page, "expected_page_version": 0}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["page_version"], 1)

        self.page.refresh_from_db()
        self.assertEqual(self.page.page_version, 1)
        self.assertIn("Naslov stranice", self.page.body_plaintext)
