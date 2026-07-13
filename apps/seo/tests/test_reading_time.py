"""Testovi za vreme čitanja."""

from django.test import TestCase

from apps.blog.models import BlogPost
from apps.seo.reading_time import (
    iso_duration_minutes,
    reading_time_for_content_object,
    reading_time_minutes,
)
from apps.seo.schema.builders import build_article_schema


class ReadingTimeTests(TestCase):
    def test_reading_time_minutes_minimum_one(self):
        self.assertEqual(reading_time_minutes(0), 1)
        self.assertEqual(reading_time_minutes(50), 1)
        self.assertEqual(reading_time_minutes(400), 2)

    def test_iso_duration_minutes(self):
        self.assertEqual(iso_duration_minutes(8), "PT8M")

    def test_reading_time_for_blog_post_with_excerpt(self):
        post = BlogPost.objects.create(
            title="Test",
            slug="test",
            excerpt=" ".join(["reč"] * 220),
        )
        self.assertEqual(reading_time_for_content_object(post), 1)

    def test_article_schema_includes_time_required(self):
        post = BlogPost.objects.create(
            title="Schema test",
            slug="schema-test",
            excerpt=" ".join(["reč"] * 400),
            is_published=True,
        )
        schema = build_article_schema(None, post, schema_type="BlogPosting")
        self.assertIsNotNone(schema)
        self.assertEqual(schema["timeRequired"], "PT2M")
