"""SEO Phase 1 — robots max-snippet, indexing toggle, no meta keywords in HTML."""

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from apps.seo.constants import RobotsMaxSnippet
from apps.seo.forms import SeoMetadataAdminForm
from apps.seo.models import SeoMetadata
from apps.seo.rendering import RENDERED_SEO_FIELDS, resolve_seo_tags
from apps.seo.robots import build_robots_meta_content, resolve_robots_directive
from apps.seo.services import build_seo_context, resolve_keywords


class RobotsMaxSnippetTests(SimpleTestCase):
    def test_omits_auto_snippet_directive(self):
        content = build_robots_meta_content()
        self.assertNotIn("max-snippet", content)

    def test_includes_max_snippet_when_set(self):
        content = build_robots_meta_content(robots_max_snippet=RobotsMaxSnippet.NONE)
        self.assertIn("max-snippet:0", content)

    def test_snippet_before_image_preview(self):
        content = build_robots_meta_content(
            robots_max_snippet=RobotsMaxSnippet.UNLIMITED,
            robots_max_image_preview="large",
        )
        snippet_index = content.index("max-snippet")
        image_index = content.index("max-image-preview")
        self.assertLess(snippet_index, image_index)


class MetaKeywordsOutputTests(SimpleTestCase):
    def test_rendered_seo_fields_exclude_keywords(self):
        self.assertNotIn("keywords", RENDERED_SEO_FIELDS)
        self.assertNotIn("focus_keyword", RENDERED_SEO_FIELDS)

    def test_meta_basic_template_omits_keywords(self):
        html = render_to_string(
            "seo/partials/meta_basic.html",
            {
                "seo": {
                    "description": "Opis stranice.",
                    "robots": "index, follow",
                    "keywords": "cement, fasada",
                    "focus_keyword": "cement",
                    "canonical": "https://example.com/",
                }
            },
        )
        self.assertIn('name="description"', html)
        self.assertIn('name="robots"', html)
        self.assertNotIn('name="keywords"', html)
        self.assertNotIn("focus-keyword", html)

    def test_resolve_keywords_still_available_for_analyzers(self):
        metadata = SeoMetadata(
            focus_keyword="cement",
            secondary_keywords="fasada, temelj",
        )
        self.assertEqual(resolve_keywords(metadata), "cement, fasada, temelj")


class SearchEngineVisibilityFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.contenttypes.models import ContentType

        from apps.blog.models import BlogPost

        cls.post = BlogPost.objects.create(title="SEO test", slug="seo-test")
        cls.content_type = ContentType.objects.get_for_model(BlogPost)

    def _base_form_data(self, allow_indexing):
        return {
            "content_type": self.content_type.pk,
            "object_id": self.post.pk,
            "seo_title": "",
            "meta_description": "",
            "focus_keyword": "",
            "secondary_keywords": "",
            "canonical_url": "",
            "robots_index": "True" if allow_indexing else "False",
            "robots_follow": "True" if allow_indexing else "False",
            "robots_nosnippet": False,
            "robots_noarchive": False,
            "robots_max_snippet": "",
                "robots_max_image_preview": "",
                "include_in_sitemap": "True",
                "og_title": "",
            "og_description": "",
            "og_type": "",
            "og_url": "",
            "twitter_title": "",
            "twitter_description": "",
            "twitter_card": "",
            "is_cornerstone": False,
            "breadcrumb_title": "",
            "schema_type": "",
        }

    def test_hide_from_google_sets_noindex_nofollow(self):
        form = SeoMetadataAdminForm(
            data=self._base_form_data(False),
            instance=SeoMetadata(content_type=self.content_type, object_id=self.post.pk),
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["robots_index"])
        self.assertFalse(form.cleaned_data["robots_follow"])

    def test_allow_indexing_sets_index_follow(self):
        data = self._base_form_data(True)
        data["robots_follow"] = "False"
        form = SeoMetadataAdminForm(
            data=data,
            instance=SeoMetadata(content_type=self.content_type, object_id=self.post.pk),
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["robots_index"])
        self.assertTrue(form.cleaned_data["robots_follow"])

    def test_initial_visibility_reflects_noindex_instance(self):
        metadata = SeoMetadata(robots_index=False, robots_follow=True)
        form = SeoMetadataAdminForm(instance=metadata)
        self.assertFalse(form.initial.get("robots_index", metadata.robots_index))


class SeoContextKeywordsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.contenttypes.models import ContentType

        from apps.blog.models import BlogPost

        cls.post = BlogPost.objects.create(title="SEO context", slug="seo-context")
        cls.content_type = ContentType.objects.get_for_model(BlogPost)
        cls.metadata = SeoMetadata.objects.create(
            content_type=cls.content_type,
            object_id=cls.post.pk,
            focus_keyword="cement",
            secondary_keywords="fasada",
        )

    def test_build_seo_context_omits_keywords(self):
        context = build_seo_context(self.post)
        self.assertNotIn("keywords", context)
        self.assertNotIn("focus_keyword", context)

    def test_resolve_robots_includes_max_snippet(self):
        metadata = SeoMetadata(robots_max_snippet=RobotsMaxSnippet.NONE)
        directive = resolve_robots_directive(metadata)
        self.assertIn("max-snippet:0", directive)

    def test_resolve_seo_tags_omits_keywords(self):
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        seo = resolve_seo_tags(request)
        self.assertNotIn("keywords", seo)
        self.assertNotIn("focus_keyword", seo)
