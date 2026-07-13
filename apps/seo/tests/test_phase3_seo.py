"""SEO Phase 3 — redirect manager, auto-redirect na promenu slug-a, AI readiness."""

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.blog.admin import BlogPostAdmin
from apps.blog.models import BlogPost
from apps.page.schema import empty_page
from apps.page.structure import (
    create_faq_block,
    create_heading_block,
    create_section,
    create_text_block,
)
from apps.seo.ai_readiness import analyze_ai_readiness
from apps.seo.analysis_ui import render_ai_readiness_html
from apps.seo.models import Redirect, RedirectType, normalize_redirect_path
from apps.seo.redirects import create_redirect_for_url_change


class NormalizeRedirectPathTests(TestCase):
    def test_adds_leading_and_trailing_slash(self):
        self.assertEqual(normalize_redirect_path("blog/stari"), "/blog/stari/")

    def test_strips_domain_and_query(self):
        self.assertEqual(
            normalize_redirect_path("https://example.com/blog/stari/?utm=x#frag"),
            "/blog/stari/",
        )

    def test_empty_returns_empty(self):
        self.assertEqual(normalize_redirect_path(""), "")


class RedirectModelTests(TestCase):
    def test_clean_rejects_same_paths(self):
        redirect = Redirect(old_path="/isti/", new_path="/isti/")
        with self.assertRaises(ValidationError):
            redirect.full_clean()

    def test_clean_requires_new_path_for_301(self):
        redirect = Redirect(old_path="/stari/", new_path="")
        with self.assertRaises(ValidationError):
            redirect.full_clean()

    def test_gone_clears_new_path(self):
        redirect = Redirect(
            old_path="/uklonjeno/",
            new_path="/negde/",
            redirect_type=RedirectType.GONE,
        )
        redirect.full_clean()
        redirect.save()
        self.assertEqual(redirect.new_path, "")

    def test_save_normalizes_paths(self):
        redirect = Redirect.objects.create(old_path="stari", new_path="novi")
        self.assertEqual(redirect.old_path, "/stari/")
        self.assertEqual(redirect.new_path, "/novi/")


class RedirectMiddlewareTests(TestCase):
    def test_301_redirect_on_404(self):
        Redirect.objects.create(old_path="/nepostojeca-stranica/", new_path="/blog/")
        response = self.client.get("/nepostojeca-stranica/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/blog/")

    def test_302_redirect_on_404(self):
        Redirect.objects.create(
            old_path="/privremeno/",
            new_path="/blog/",
            redirect_type=RedirectType.TEMPORARY,
        )
        response = self.client.get("/privremeno/")
        self.assertEqual(response.status_code, 302)

    def test_410_gone(self):
        Redirect.objects.create(
            old_path="/uklonjena-stranica/",
            redirect_type=RedirectType.GONE,
        )
        response = self.client.get("/uklonjena-stranica/")
        self.assertEqual(response.status_code, 410)

    def test_inactive_redirect_is_skipped(self):
        Redirect.objects.create(
            old_path="/neaktivno/",
            new_path="/blog/",
            is_active=False,
        )
        response = self.client.get("/neaktivno/")
        self.assertEqual(response.status_code, 404)

    def test_path_without_trailing_slash_matches(self):
        Redirect.objects.create(old_path="/stara-putanja/", new_path="/blog/")
        response = self.client.get("/stara-putanja", follow=False)
        # CommonMiddleware može prvo dodati kosu crtu; u oba slučaja stižemo do cilja.
        self.assertIn(response.status_code, (301, 302))


class AutoRedirectHelperTests(TestCase):
    def test_creates_permanent_redirect(self):
        redirect = create_redirect_for_url_change("/blog/stari/", "/blog/novi/")
        self.assertIsNotNone(redirect)
        self.assertEqual(redirect.old_path, "/blog/stari/")
        self.assertEqual(redirect.new_path, "/blog/novi/")
        self.assertEqual(redirect.redirect_type, RedirectType.PERMANENT)

    def test_same_paths_returns_none(self):
        self.assertIsNone(create_redirect_for_url_change("/blog/isti/", "/blog/isti/"))

    def test_flattens_chains(self):
        create_redirect_for_url_change("/blog/a/", "/blog/b/")
        create_redirect_for_url_change("/blog/b/", "/blog/c/")

        first = Redirect.objects.get(old_path="/blog/a/")
        self.assertEqual(first.new_path, "/blog/c/")

    def test_removes_shadowing_redirect(self):
        # Stranica se vraća na staru putanju — preusmerenje sa nje se briše.
        create_redirect_for_url_change("/blog/x/", "/blog/y/")
        create_redirect_for_url_change("/blog/y/", "/blog/x/")

        self.assertFalse(Redirect.objects.filter(old_path="/blog/x/").exists())
        self.assertEqual(
            Redirect.objects.get(old_path="/blog/y/").new_path,
            "/blog/x/",
        )


class BlogSlugChangeRedirectTests(TestCase):
    def _admin_request(self):
        request = RequestFactory().post("/")
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_slug_change_creates_redirect(self):
        post = BlogPost.objects.create(
            title="Originalni naslov",
            slug="originalni-naslov",
            is_published=True,
            publish_date=timezone.localdate(),
        )
        model_admin = BlogPostAdmin(BlogPost, AdminSite())

        post.slug = "novi-naslov"
        model_admin.save_model(self._admin_request(), post, form=None, change=True)

        old_url = reverse("frontend:blog_detail", kwargs={"slug": "originalni-naslov"})
        redirect = Redirect.objects.get(old_path=old_url)
        self.assertEqual(
            redirect.new_path,
            reverse("frontend:blog_detail", kwargs={"slug": "novi-naslov"}),
        )
        self.assertEqual(redirect.redirect_type, RedirectType.PERMANENT)

    def test_draft_slug_change_does_not_create_redirect(self):
        post = BlogPost.objects.create(
            title="Bez naslova",
            slug="nacrt-abc123def456",
            is_published=False,
        )
        model_admin = BlogPostAdmin(BlogPost, AdminSite())

        post.title = "Pravi naslov"
        model_admin.save_model(self._admin_request(), post, form=None, change=True)

        self.assertEqual(Redirect.objects.count(), 0)

    def test_unchanged_slug_does_not_create_redirect(self):
        post = BlogPost.objects.create(title="Stabilan", slug="stabilan-slug")
        model_admin = BlogPostAdmin(BlogPost, AdminSite())

        model_admin.save_model(self._admin_request(), post, form=None, change=True)

        self.assertEqual(Redirect.objects.count(), 0)


def _build_rich_body_page():
    page = empty_page()
    section = create_section()
    column = section["rows"][0]["columns"][0]

    intro_text = (
        "Cementna košuljica je završni sloj poda koji izravnava površinu i priprema "
        "je za postavljanje finalne obloge. U ovom vodiču objašnjavamo kada je "
        "potrebna, koliko traje sušenje i koje debljine se preporučuju za stambene "
        "i poslovne prostore."
    )
    body_text = (
        "Za stambene prostore preporučuje se debljina od četiri do šest centimetara. "
        "Sušenje traje otprilike sedam dana po centimetru debljine, u zavisnosti od "
        "temperature i vlažnosti prostorije. Pre postavljanja parketa ili pločica "
        "obavezno proverite vlažnost košuljice merenjem. " * 6
    )

    column["blocks"] = [
        create_text_block(text=intro_text),
        create_heading_block(level=2, text="Kada je potrebna cementna košuljica?"),
        create_text_block(text=body_text),
        create_heading_block(level=2, text="Koliko traje sušenje?"),
        create_text_block(text=body_text),
        create_faq_block(),
    ]
    page["sections"] = [section]
    return page


class AiReadinessTests(TestCase):
    def test_unsaved_object_returns_message(self):
        result = analyze_ai_readiness(BlogPost())
        self.assertEqual(result.score, 0)
        self.assertTrue(result.message)
        self.assertEqual(result.checks, [])

    def test_rich_content_scores_well(self):
        post = BlogPost.objects.create(
            title="Cementna košuljica — kompletan vodič",
            slug="cementna-kosuljica-vodic",
            is_published=True,
            publish_date=timezone.localdate(),
        )
        post.apply_body_page(_build_rich_body_page())
        post.save()

        result = analyze_ai_readiness(post)
        self.assertGreaterEqual(result.score, 70)

        check_ids = [check.check_id for check in result.checks]
        for expected in (
            "ai_h1",
            "ai_first_paragraph",
            "ai_headings",
            "ai_faq",
            "ai_schema",
            "ai_content_depth",
        ):
            self.assertIn(expected, check_ids)

        faq_check = next(check for check in result.checks if check.check_id == "ai_faq")
        self.assertEqual(faq_check.status.value, "good")

    def test_empty_content_scores_low(self):
        post = BlogPost.objects.create(title="Prazan", slug="prazan-post")
        result = analyze_ai_readiness(post)
        self.assertLess(result.score, 70)

        depth_check = next(
            check for check in result.checks if check.check_id == "ai_content_depth"
        )
        self.assertEqual(depth_check.status.value, "bad")

    def test_to_dict_contains_status_labels(self):
        post = BlogPost.objects.create(title="Dict test", slug="dict-test")
        data = analyze_ai_readiness(post).to_dict()
        self.assertIn("score", data)
        self.assertTrue(all("status_label" in check for check in data["checks"]))

    def test_render_html_contains_score(self):
        post = BlogPost.objects.create(title="Render test", slug="render-test")
        result = analyze_ai_readiness(post)
        html = render_ai_readiness_html(result)
        self.assertIn("data-seo-ai-readiness-analyzer", html)
        self.assertIn(str(result.score), html)
