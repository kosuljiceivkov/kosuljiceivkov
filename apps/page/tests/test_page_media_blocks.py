"""Testovi za video, FAQ i image blokove."""

from django.test import RequestFactory, TestCase

from apps.page.catalog.elements import build_builder_catalog
from apps.page.rendering import get_page_renderer
from apps.page.rendering.base import RenderContext
from apps.page.schema import empty_page
from apps.page.structure import (
    create_faq_block,
    create_image_block,
    create_section,
    create_text_block,
    create_video_block,
)
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
        block["attrs"]["src"] = "/media/page/document/demo.jpg"
        block["attrs"]["alt"] = "Demo slika"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn('alt="Demo slika"', html)

    def test_renders_image_with_custom_width_percent(self):
        block = create_image_block()
        block["attrs"]["src"] = "/media/page/document/demo.jpg"
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

    def test_renders_uploaded_video_in_native_ratio_with_poster(self):
        block = create_video_block()
        block["attrs"]["src"] = "/media/page/videos/demo.mp4"
        block["attrs"]["poster"] = "/media/page/document/video-poster.jpg"

        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )

        self.assertIn("iv-page-video--file", html)
        self.assertIn('poster="http://testserver/media/page/document/video-poster.jpg"', html)
        self.assertIn('src="http://testserver/media/page/videos/demo.mp4"', html)

    def test_saved_spacing_settings_do_not_affect_rendering(self):
        page = self._page_with_block(create_text_block(text="Razmaci"))
        section = page["sections"][0]
        section["settings"]["row_gap"] = "lg"
        section["settings"]["padding_top"] = 11
        row = section["rows"][0]
        row["settings"]["column_gap"] = 16
        row["columns"][0]["settings"]["padding"] = 17

        validate_page_or_raise(page)
        html = self.renderer.render(page, context=RenderContext(request=self.request))

        self.assertNotIn("iv-page-section--row-gap", html)
        self.assertNotIn("iv-page-row--gap", html)
        self.assertNotIn("iv-page-col--pad", html)
        self.assertNotIn('style="', html)

    def test_builder_catalog_has_no_spacing_controls(self):
        catalog = build_builder_catalog()
        field_ids = {
            field["id"]
            for group in ("section_settings", "row_settings", "column_settings")
            for field in catalog[group]
        }

        self.assertTrue(
            {
                "padding_top",
                "padding_bottom",
                "margin_top",
                "margin_bottom",
                "row_gap",
                "column_gap",
                "padding",
            }.isdisjoint(field_ids)
        )

    def test_new_sections_do_not_store_spacing_settings(self):
        section = create_section()

        self.assertNotIn("padding_top", section["settings"])
        self.assertNotIn("padding_bottom", section["settings"])
        self.assertNotIn("margin_bottom", section["settings"])
        self.assertNotIn("row_gap", section["settings"])
        self.assertNotIn("column_gap", section["rows"][0]["settings"])
        self.assertNotIn("padding", section["rows"][0]["columns"][0]["settings"])

    def test_new_columns_and_blocks_are_centered_by_default(self):
        section = create_section()
        column = section["rows"][0]["columns"][0]
        block = create_text_block(text="Centrirano")

        self.assertEqual(column["settings"]["horizontal_align"], "center")
        self.assertEqual(block["settings"]["align"], "center")

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

        with self.assertRaises(PageValidationError) as ctx:
            validate_page_or_raise(self._page_with_block(block))

        message = "; ".join(ctx.exception.errors)
        self.assertIn("slika mora imati alt tekst", message.lower())
        self.assertNotIn("sections[", message)
        self.assertNotIn("blocks[", message)

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

    def test_button_alignment_is_rendered(self):
        from apps.page.structure import create_button_block

        block = create_button_block()
        block["attrs"]["label"] = "CTA"
        block["attrs"]["href"] = "/kontakt/"
        block["settings"]["align"] = "right"
        html = self.renderer.render(
            self._page_with_block(block),
            context=RenderContext(request=self.request),
        )
        self.assertIn("iv-page-button-wrap--align-right", html)

    def test_section_hex_background_renders_inline_style(self):
        page = self._page_with_block(create_text_block(text="Colored"))
        page["sections"][0]["settings"]["background_color"] = "#e8f1ff"
        html = self.renderer.render(page, context=RenderContext(request=self.request))
        self.assertIn("iv-page-section--bg-custom", html)
        self.assertIn("background-color: #e8f1ff", html)
