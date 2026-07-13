"""Test rich text rendering for text blocks."""

from django.test import RequestFactory, TestCase

from apps.page.rendering import get_page_renderer
from apps.page.rendering.base import RenderContext
from apps.page.structure import create_text_block
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
