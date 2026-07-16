"""SEO Phase 3 — AI readiness (redirect manager uklonjen)."""

from django.test import TestCase
from django.utils import timezone

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
