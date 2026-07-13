"""Testovi za page save API."""

from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.page.structure import create_heading_block, create_section, create_text_block
from apps.page.tests.fixtures import sample_page


class PageSaveApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        self.post = BlogPost.objects.create(
            title="Visual",
            slug="visual",
        )

    def _page_save_url(self) -> str:
        return reverse("admin:blog_blogpost_page_save", args=[self.post.pk])

    def test_page_save_persists_page_and_increments_version(self):
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

        self.post.refresh_from_db()
        self.assertEqual(self.post.page_version, 1)
        self.assertIn("Naslov stranice", self.post.body_plaintext)

    def test_page_save_accepts_structure_first_page(self):
        section = create_section()
        section["rows"][0]["columns"][0]["blocks"] = [
            create_heading_block(text="Test naslov"),
            create_text_block(text="Test tekst"),
        ]
        page = {"format": "iv_page_v1", "type": "page", "sections": [section]}

        response = self.client.post(
            self._page_save_url(),
            data=json.dumps({"body_page": page, "expected_page_version": 0}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(
            self.post.body_page["sections"][0]["rows"][0]["columns"][0]["blocks"][0]["attrs"]["text"],
            "Test naslov",
        )
