"""SEO Phase 2 — slug analyzer, sitemap toggle, OG platforms, lazy-loading audit."""

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.template.loader import render_to_string
from django.test import TestCase

from apps.page.schema import empty_page
from apps.page.structure import create_image_block, create_section
from apps.blog.models import BlogPost
from apps.seo.analysis_ui import render_open_graph_preview_html
from apps.seo.constants import DEFAULT_OG_PREVIEW_PLATFORM
from apps.seo.forms import SeoMetadataAdminForm
from apps.seo.image_seo import analyze_image_seo
from apps.seo.image_seo_content import PageImageEntry, _assign_loading_defaults
from apps.seo.models import SeoMetadata
from apps.seo.open_graph import OpenGraphTags
from apps.seo.sitemap_filters import exclude_seo_hidden
from apps.seo.sitemaps import BlogPostSitemap
from apps.seo.slug_analyzer import analyze_slug


class SlugAnalyzerTests(TestCase):
    def test_valid_slug_scores_well(self):
        result = analyze_slug("cementne-kosuljice-fasada", focus_keyword="cementne kosuljice")
        self.assertGreaterEqual(result.score, 70)
        self.assertTrue(any(check.check_id == "slug_charset" for check in result.checks))

    def test_invalid_slug_characters_fail(self):
        result = analyze_slug("Cementne_Košuljice!")
        charset = next(check for check in result.checks if check.check_id == "slug_charset")
        self.assertEqual(charset.status.value, "bad")

    def test_duplicate_slug_detected(self):
        BlogPost.objects.create(title="Postoji", slug="postoji-slug")
        result = analyze_slug("postoji-slug")
        unique = next(check for check in result.checks if check.check_id == "slug_unique")
        self.assertEqual(unique.status.value, "bad")


class SitemapToggleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.visible = BlogPost.objects.create(
            title="Vidljiv",
            slug="vidljiv-post",
            is_published=True,
            publish_date=timezone.localdate(),
        )
        cls.hidden = BlogPost.objects.create(
            title="Sakriven",
            slug="sakriven-post",
            is_published=True,
            publish_date=timezone.localdate(),
        )
        content_type = ContentType.objects.get_for_model(BlogPost)
        SeoMetadata.objects.create(
            content_type=content_type,
            object_id=cls.hidden.pk,
            robots_index=False,
            include_in_sitemap=False,
        )

    def test_exclude_seo_hidden_removes_noindex_posts(self):
        slugs = list(
            exclude_seo_hidden(BlogPost.objects.publicly_visible(), BlogPost).values_list(
                "slug",
                flat=True,
            )
        )
        self.assertIn(self.visible.slug, slugs)
        self.assertNotIn(self.hidden.slug, slugs)

    def test_blog_sitemap_uses_seo_filter(self):
        slugs = [post.slug for post in BlogPostSitemap().items()]
        self.assertIn(self.visible.slug, slugs)
        self.assertNotIn(self.hidden.slug, slugs)

    def test_hide_from_google_clears_sitemap_flag(self):
        content_type = ContentType.objects.get_for_model(BlogPost)
        post = BlogPost.objects.create(title="Form test", slug="form-test")
        form = SeoMetadataAdminForm(
            data={
                "content_type": content_type.pk,
                "object_id": post.pk,
                "seo_title": "",
                "meta_description": "",
                "focus_keyword": "",
                "secondary_keywords": "",
                "canonical_url": "",
                "robots_index": "False",
                "robots_follow": "False",
                "include_in_sitemap": "True",
                "robots_nosnippet": False,
                "robots_noarchive": False,
                "robots_max_snippet": "",
                "robots_max_image_preview": "",
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
            },
            instance=SeoMetadata(content_type=content_type, object_id=post.pk),
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["include_in_sitemap"])


class OgPlatformPreviewTests(TestCase):
    def test_render_includes_platform_tabs(self):
        tags = OpenGraphTags(
            og_type="article",
            og_title="Naslov za deljenje na društvenim mrežama",
            og_description="Opis objave za deljenje.",
            og_url="https://example.com/blog/test/",
            og_image="",
            sources={},
        )
        html = render_open_graph_preview_html(tags, platform=DEFAULT_OG_PREVIEW_PLATFORM)
        self.assertIn("data-og-platform", html)
        self.assertIn("Facebook", html)
        self.assertIn("LinkedIn", html)
        self.assertIn("WhatsApp", html)

    def test_meta_basic_still_omits_keywords(self):
        html = render_to_string(
            "seo/partials/meta_basic.html",
            {
                "seo": {
                    "description": "Opis.",
                    "robots": "index, follow",
                    "keywords": "test",
                }
            },
        )
        self.assertNotIn('name="keywords"', html)


class LazyLoadingAuditTests(TestCase):
    def test_assign_loading_defaults_first_builder_image_eager(self):
        images = _assign_loading_defaults(
            [
                PageImageEntry(
                    source="page_image",
                    label="Slika #1",
                    alt_text="Prva",
                    filename="a.jpg",
                    basename="a.jpg",
                    width=None,
                    height=None,
                    file_size=0,
                    format_name="",
                ),
                PageImageEntry(
                    source="page_image",
                    label="Slika #2",
                    alt_text="Druga",
                    filename="b.jpg",
                    basename="b.jpg",
                    width=None,
                    height=None,
                    file_size=0,
                    format_name="",
                ),
            ]
        )
        self.assertEqual(images[0].loading, "eager")
        self.assertEqual(images[1].loading, "lazy")

    def test_analyze_image_seo_includes_lazy_loading_check(self):
        post = BlogPost.objects.create(title="Slike", slug="slike-test")
        page = empty_page()
        section = create_section()
        column = section["rows"][0]["columns"][0]
        first_image = create_image_block()
        first_image["attrs"]["src"] = "/media/blog/test-a.jpg"
        first_image["attrs"]["alt"] = "Prva slika"
        second_image = create_image_block()
        second_image["attrs"]["src"] = "/media/blog/test-b.jpg"
        second_image["attrs"]["alt"] = "Druga slika"
        column["blocks"] = [first_image, second_image]
        page["sections"] = [section]
        post.apply_body_page(page)
        post.save()

        result = analyze_image_seo(post)
        check_ids = [check.check_id for check in result.checks]
        self.assertIn("lazy_loading", check_ids)
        self.assertTrue(any(row.get("loading") == "eager" for row in result.images))
