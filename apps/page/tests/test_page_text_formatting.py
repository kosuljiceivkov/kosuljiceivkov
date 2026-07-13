"""Test rich text rendering for text and heading blocks."""

from django.test import RequestFactory

from apps.page.normalize import normalize_page
from apps.page.plaintext import extract_page_plaintext
from apps.page.rendering import get_page_renderer
from apps.page.rendering.base import RenderContext
from apps.page.structure import create_heading_block, create_text_block
from apps.page.tests.test_page_media_blocks import PageMediaBlockTests


class PageTextFormattingTests(PageMediaBlockTests):
    def setUp(self):
        super().setUp()
        self.renderer = get_page_renderer("html")
        self.request = RequestFactory().get("/")

    def test_renders_text_with_inline_font_size_and_formatting(self):
        block = create_text_block()
        block["attrs"]["text"] = 'Normal <span style="font-size: 22px">big</span> text'

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn('<span style="font-size: 22px">', html)
        self.assertIn("big", html)

    def test_renders_heading_with_inline_font_size_and_formatting(self):
        block = create_heading_block(level=2)
        block["attrs"]["text"] = (
            '<b>Bold</b> <i>italic</i> <u>under</u> '
            '<span style="font-size: 28px">large</span>'
        )

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn("<h2", html)
        self.assertIn("iv-page-heading", html)
        self.assertIn("<b>Bold</b>", html)
        self.assertIn("<i>italic</i>", html)
        self.assertIn("<u>under</u>", html)
        self.assertIn('<span style="font-size: 28px">', html)
        self.assertIn("large", html)

    def test_normalize_sanitizes_heading_inline_html(self):
        block = create_heading_block(level=1)
        block["attrs"]["text"] = (
            'Safe <script>alert(1)</script><span style="font-size: 40px; color: red">'
            "Sized</span>"
        )
        page = normalize_page(self._page_with_block(block))
        text = page["sections"][0]["rows"][0]["columns"][0]["blocks"][0]["attrs"]["text"]

        self.assertNotIn("<script>", text)
        self.assertIn('<span style="font-size: 40px">', text)
        self.assertNotIn("color:", text)

    def test_heading_plaintext_strips_tags(self):
        block = create_heading_block(level=3)
        block["attrs"]["text"] = '<span style="font-size: 20px"><b>Naslov</b></span>'
        page = self._page_with_block(block)

        self.assertEqual(extract_page_plaintext(page), "Naslov")
