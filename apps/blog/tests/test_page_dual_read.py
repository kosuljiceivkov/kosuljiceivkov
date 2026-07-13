"""Javni prikaz za visual builder objave."""

from django.test import TestCase
from django.utils import timezone

from apps.blog.models import BlogPost
from apps.page.tests.fixtures import sample_page


class BlogPagePublicRenderTests(TestCase):
    def _create_published_post(self, **kwargs) -> BlogPost:
        defaults = {
            "title": "Objava",
            "slug": "objava-page",
            "is_published": True,
            "publish_date": timezone.localdate(),
        }
        defaults.update(kwargs)
        return BlogPost.objects.create(**defaults)

    def test_visual_builder_post_renders_iv_page(self):
        post = self._create_published_post(slug="visual-post")
        post.apply_body_page(sample_page())
        post.save()

        response = self.client.get(post.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-iv-page")
        self.assertContains(response, "Naslov stranice")
        self.assertContains(response, "Spremni za sledeći korak?")
        self.assertNotContains(response, "data-page-builder")
