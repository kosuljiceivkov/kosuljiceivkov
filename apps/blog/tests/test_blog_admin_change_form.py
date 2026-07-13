"""Testovi BlogPost admin change form integracije."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.blog.admin_change import (
    DRAFT_SLUG_PREFIX,
    DRAFT_TITLE_PLACEHOLDER,
    build_blog_change_form_context,
    create_visual_builder_draft,
    is_placeholder_draft,
    maybe_update_slug_from_title,
    unique_slug_for_title,
)
from apps.blog.models import BlogPost
from apps.page.tests.fixtures import sample_page


class BlogAdminChangeHelpersTests(TestCase):
    def test_create_visual_builder_draft(self):
        draft = create_visual_builder_draft()

        self.assertTrue(draft.pk)
        self.assertEqual(draft.title, DRAFT_TITLE_PLACEHOLDER)
        self.assertTrue(draft.slug.startswith(DRAFT_SLUG_PREFIX))

    def test_is_placeholder_draft(self):
        draft = create_visual_builder_draft()
        self.assertTrue(is_placeholder_draft(draft))

        draft.title = "Pravi naslov"
        self.assertFalse(is_placeholder_draft(draft))

    def test_unique_slug_for_title_avoids_collisions(self):
        BlogPost.objects.create(title="Test", slug="test-slug")
        slug = unique_slug_for_title("Test slug")
        self.assertEqual(slug, "test-slug-2")

    def test_maybe_update_slug_from_title_replaces_draft_slug(self):
        draft = create_visual_builder_draft()
        draft.title = "Kako izabrati košuljicu"
        maybe_update_slug_from_title(draft)

        self.assertEqual(draft.slug, "kako-izabrati-kosuljicu")

    def test_build_blog_change_form_context_for_visual_post(self):
        post = BlogPost.objects.create(title="Visual", slug="visual")
        post.apply_body_page(sample_page())
        post.save()

        context = build_blog_change_form_context(None, post)

        self.assertIn("page/save", context["blog_page_save_url"])
        self.assertIn("page/upload-image", context["blog_upload_url"])
        self.assertIn('"format": "iv_page_v1"', context["blog_initial_page_json"])
        self.assertFalse(context["blog_focus_title"])

    def test_build_blog_change_form_context_includes_draft_constants(self):
        post = create_visual_builder_draft()
        context = build_blog_change_form_context(None, post)

        self.assertEqual(context["blog_draft_title_placeholder"], DRAFT_TITLE_PLACEHOLDER)
        self.assertEqual(context["blog_draft_slug_prefix"], DRAFT_SLUG_PREFIX)


class BlogPostAdminChangeFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="blog-admin",
            email="blog-admin@example.com",
            password="password",
        )
        self.client.force_login(self.user)

    def test_add_redirects_to_visual_builder_draft_change_form(self):
        response = self.client.get(reverse("admin:blog_blogpost_add"))

        self.assertEqual(response.status_code, 302)
        post = BlogPost.objects.get()
        self.assertRedirects(
            response,
            reverse("admin:blog_blogpost_change", args=[post.pk]),
        )

    def test_visual_change_form_renders_builder_shell(self):
        post = create_visual_builder_draft()
        response = self.client.get(reverse("admin:blog_blogpost_change", args=[post.pk]))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("data-blog-page-builder", content)
        self.assertIn("blog_page_builder.js", content)
        self.assertIn('id="blog-initial-page"', content)
        self.assertIn("page/upload-image", content)
        self.assertNotIn("blog-document-editor.bundle.js", content)

    def test_change_form_includes_preview_link(self):
        post = create_visual_builder_draft()
        response = self.client.get(reverse("admin:blog_blogpost_change", args=[post.pk]))

        self.assertContains(response, reverse("frontend:admin_preview_blog", args=[post.pk]))

    def test_save_model_updates_draft_slug_from_title(self):
        from django.contrib import admin as django_admin
        from unittest.mock import Mock

        from apps.blog.admin import BlogPostAdmin

        post = create_visual_builder_draft()
        post.title = "Naslov novog članka"
        request = self.client.request()
        request.user = self.user

        model_admin = BlogPostAdmin(BlogPost, django_admin.site)
        model_admin.save_model(request, post, Mock(), change=True)

        post.refresh_from_db()
        self.assertEqual(post.slug, "naslov-novog-clanka")
