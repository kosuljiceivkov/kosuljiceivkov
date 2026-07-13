"""Stabilization — regression testovi za production blockere."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.blog.admin_change import DRAFT_SLUG_PREFIX, DRAFT_TITLE_PLACEHOLDER, create_visual_builder_draft
from apps.blog.admin_forms import BlogPostAdminForm
from apps.blog.models import BlogPost


class BlogPostAdminFormTests(TestCase):
    def _form_data(self, post, *, is_published: bool) -> dict:
        return {
            "title": post.title,
            "slug": post.slug,
            "publish_date": timezone.localdate().isoformat(),
            "is_published": is_published,
        }

    def test_publish_blocked_with_placeholder_title(self):
        post = create_visual_builder_draft()
        form = BlogPostAdminForm(
            data={
                **self._form_data(post, is_published=True),
                "title": DRAFT_TITLE_PLACEHOLDER,
            },
            instance=post,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_publish_blocked_with_draft_slug(self):
        post = BlogPost.objects.create(
            title="Pravi naslov",
            slug=f"{DRAFT_SLUG_PREFIX}abc123",
            is_published=False,
        )
        form = BlogPostAdminForm(
            data=self._form_data(post, is_published=True),
            instance=post,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("slug", form.errors)

    def test_draft_save_allowed_with_placeholder_title(self):
        post = create_visual_builder_draft()
        form = BlogPostAdminForm(
            data=self._form_data(post, is_published=False),
            instance=post,
        )

        self.assertTrue(form.is_valid())


class BlogPostAdminStabilizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="stabilization-admin",
            email="stabilization@example.com",
            password="password",
        )
        self.client.force_login(self.user)

    def test_change_form_includes_draft_constants_for_client(self):
        post = create_visual_builder_draft()
        response = self.client.get(reverse("admin:blog_blogpost_change", args=[post.pk]))

        self.assertContains(response, f'data-draft-title-placeholder="{DRAFT_TITLE_PLACEHOLDER}"')
        self.assertContains(response, f'data-draft-slug-prefix="{DRAFT_SLUG_PREFIX}"')
        self.assertContains(response, "data-blog-blocker")

    def test_publish_blocked_server_side_with_placeholder_title(self):
        post = create_visual_builder_draft()
        post.save()

        response = self.client.post(
            reverse("admin:blog_blogpost_change", args=[post.pk]),
            data={
                "title": DRAFT_TITLE_PLACEHOLDER,
                "slug": post.slug,
                "is_published": "on",
                "publish_date": timezone.localdate().isoformat(),
                "_save": "Sačuvaj",
            },
        )

        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertFalse(post.is_published)
        self.assertContains(response, "Bez naslova")
