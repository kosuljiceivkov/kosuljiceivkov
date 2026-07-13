"""Testovi za inline rich text sanitizaciju."""

from django.test import SimpleTestCase

from apps.page.rich_text import inline_html_to_plaintext, sanitize_inline_html


class RichTextSanitizerTests(SimpleTestCase):
    def test_plain_text_is_escaped(self):
        self.assertEqual(sanitize_inline_html('Hello & "world"'), "Hello &amp; &quot;world&quot;")

    def test_allowed_inline_tags_preserved(self):
        html = sanitize_inline_html("Text <strong>bold</strong> and <em>italic</em> plus <u>line</u>")
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn("<u>line</u>", html)

    def test_span_font_size_preserved(self):
        html = sanitize_inline_html('Size <span style="font-size: 22px">big</span>')
        self.assertIn('<span style="font-size: 22px">', html)

    def test_invalid_span_font_size_removed(self):
        html = sanitize_inline_html('<span style="font-size: 200px">big</span>')
        self.assertNotIn("<span", html)
        self.assertIn("big", html)

    def test_disallowed_tags_stripped(self):
        html = sanitize_inline_html('<script>alert(1)</script><b>safe</b>')
        self.assertNotIn("script", html)
        self.assertIn("<b>safe</b>", html)

    def test_inline_html_to_plaintext(self):
        self.assertEqual(
            inline_html_to_plaintext("<strong>Bold</strong> text"),
            "Bold text",
        )
