"""Testovi za video, FAQ i image blokove."""

from django.test import RequestFactory, TestCase

from apps.page.rendering import get_page_renderer
from apps.page.rendering.base import RenderContext
from apps.page.schema import empty_page
from apps.page.structure import create_faq_block, create_image_block, create_video_block
from apps.page.validation import PageValidationError, validate_page_or_raise


class PageMediaBlockTests(TestCase):
    def setUp(self):
        self.renderer = get_page_renderer("html")
        self.request = RequestFactory().get("/")

    def _page_with_block(self, block):
        page = empty_page()
        page["sections"] = [
            {
                "id": "sec_1",
                "settings": {
                    "padding_top": "md",
                    "padding_bottom": "md",
                    "margin_top": "none",
                    "margin_bottom": "none",
                    "background": "default",
                    "container_width": "contained",
                },
                "rows": [
                    {
                        "id": "row_1",
                        "settings": {"column_gap": "md", "vertical_align": "top"},
                        "columns": [
                            {
                                "id": "col_1",
                                "settings": {
                                    "width_mobile": 12,
                                    "width_tablet": 12,
                                    "width_desktop": 12,
                                    "padding": "none",
                                    "horizontal_align": "left",
                                },
                                "blocks": [block],
                            }
                        ],
                    }
                ],
            }
        ]
        return page

    def test_renders_video_block(self):
        block = create_video_block()
        block["attrs"]["url"] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        block["attrs"]["caption"] = "Demo video"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn("iv-page-video", html)
        self.assertIn("youtube.com/embed/", html)
        self.assertIn("Demo video", html)

    def test_renders_faq_accordion(self):
        block = create_faq_block()
        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn("iv-page-faq--accordion", html)
        self.assertIn("Prvo pitanje?", html)
        self.assertIn("<details", html)

    def test_renders_image_with_alt(self):
        block = create_image_block()
        block["attrs"]["src"] = "/media/blog/document/demo.jpg"
        block["attrs"]["alt"] = "Demo slika"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn('alt="Demo slika"', html)

    def test_renders_image_with_custom_width_percent(self):
        block = create_image_block()
        block["attrs"]["src"] = "/media/blog/document/demo.jpg"
        block["attrs"]["alt"] = "Demo slika"
        block["settings"]["width_percent"] = "42"
        block["settings"]["align"] = "center"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn('style="width: 42%;"', html)
        self.assertIn("iv-page-media--align-center", html)

    def test_renders_video_with_custom_width_percent(self):
        block = create_video_block()
        block["attrs"]["url"] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        block["settings"]["width_percent"] = "75"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn('style="width: 75%;"', html)

    def test_invalid_width_percent_fails_validation(self):
        block = create_image_block()
        block["attrs"]["src"] = "/media/demo.jpg"
        block["attrs"]["alt"] = "Alt"
        block["settings"]["width_percent"] = "5"

        with self.assertRaises(PageValidationError):
            validate_page_or_raise(self._page_with_block(block))

    def test_image_without_alt_fails_validation(self):
        block = create_image_block()
        block["attrs"]["src"] = "/media/demo.jpg"
        block["attrs"]["alt"] = ""

        with self.assertRaises(PageValidationError):
            validate_page_or_raise(self._page_with_block(block))

    def test_invalid_video_url_fails_validation(self):
        block = create_video_block()
        block["attrs"]["url"] = "https://example.com/not-youtube"

        with self.assertRaises(PageValidationError):
            validate_page_or_raise(self._page_with_block(block))

    def test_renders_button_block(self):
        from apps.page.structure import create_button_block

        block = create_button_block()
        block["attrs"]["label"] = "Kontakt"
        block["attrs"]["href"] = "/kontakt/"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn("iv-page-button", html)
        self.assertIn("Kontakt", html)
        self.assertIn("/kontakt/", html)
