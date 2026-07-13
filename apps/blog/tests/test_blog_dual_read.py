"""Javni prikaz blog članaka sa visual builder sadržajem."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import BlogPost
from apps.page.tests.fixtures import sample_page


class BlogPublicRenderTests(TestCase):
    def _create_published_post(self, **kwargs) -> BlogPost:
        defaults = {
            "title": "Objava",
            "slug": "objava",
            "is_published": True,
            "publish_date": timezone.localdate(),
        }
        defaults.update(kwargs)
        return BlogPost.objects.create(**defaults)

    def test_visual_post_renders_page_content(self):
        post = self._create_published_post(slug="visual-post")
        post.apply_body_page(sample_page())
        post.save()

        response = self.client.get(post.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-iv-page")
        self.assertNotContains(response, "data-page-builder")

    def test_unpublished_post_returns_404(self):
        post = self._create_published_post(slug="draft-post", is_published=False)
        post.apply_body_page(sample_page())
        post.save()

        response = self.client.get(post.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_staff_preview_renders_visual_post(self):
        user = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="password",
        )
        post = BlogPost.objects.create(
            title="Preview visual",
            slug="preview-visual",
            is_published=False,
        )
        post.apply_body_page(sample_page())
        post.save()

        self.client.force_login(user)
        response = self.client.get(reverse("frontend:admin_preview_blog", args=[post.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-iv-page")
