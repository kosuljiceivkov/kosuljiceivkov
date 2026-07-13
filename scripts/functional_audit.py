#!/usr/bin/env python
"""Production functional audit — behavioral verification via HTTP/API."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.contenttypes.models import ContentType  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402
from PIL import Image  # noqa: E402

from apps.blog.models import BlogPost  # noqa: E402
from apps.page.tests.fixtures import sample_page  # noqa: E402
from apps.seo.models import SeoMetadata  # noqa: E402


@dataclass
class AuditResult:
    area: str
    feature: str
    status: str  # PASS | FAIL | PARTIAL
    note: str = ""


RESULTS: list[AuditResult] = []


def record(area: str, feature: str, status: str, note: str = "") -> None:
    RESULTS.append(AuditResult(area, feature, status, note))
    mark = {"PASS": "+", "FAIL": "X", "PARTIAL": "~"}[status]
    print(f"[{mark}] {area} / {feature}: {status}" + (f" — {note}" if note else ""))


def make_image(name: str = "audit.jpg") -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (12, 12), color="red").save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/jpeg")


def main() -> int:
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser("audit-admin", "audit@example.com", "password")

    client = Client()
    client.force_login(user)

    add_resp = client.get(reverse("admin:blog_blogpost_add"))
    record("BLOG", "Create new article (add redirects to draft)", "PASS" if add_resp.status_code in (200, 302) else "FAIL")

    post = BlogPost.objects.create(
        title="Audit članak",
        slug="audit-clanak",
        is_published=False,
    )
    post.apply_body_page(sample_page())
    post.save()

    ct = ContentType.objects.get_for_model(BlogPost)
    SeoMetadata.objects.get_or_create(
        content_type=ct,
        object_id=post.pk,
        defaults={"focus_keyword": "linkom"},
    )

    change_url = reverse("admin:blog_blogpost_change", args=[post.pk])
    change_resp = client.get(change_url)
    html = change_resp.content.decode("utf-8")
    record("BLOG", "Open visual builder change form", "PASS" if change_resp.status_code == 200 else "FAIL")
    record(
        "EDITOR",
        "Page builder loaded",
        "PASS" if "blog_page_builder.js" in html and "data-blog-page-builder" in html else "FAIL",
    )
    record(
        "DRAWERS",
        "Details / SEO / Publish rail buttons",
        "PASS"
        if all(x in html for x in ("data-blog-drawer-trigger=\"details\"", "data-blog-drawer-trigger=\"seo\"", "data-blog-drawer-trigger=\"publish\""))
        else "FAIL",
    )

    static_paths = re.findall(r'/static/[^"\']+', html)
    missing_static = []
    for path in sorted(set(static_paths)):
        resp = client.get(path)
        if resp.status_code != 200:
            missing_static.append(f"{path} -> {resp.status_code}")
    record(
        "ERRORS",
        "Change form static assets",
        "PASS" if not missing_static else "FAIL",
        "; ".join(missing_static[:5]),
    )

    page_save_url = reverse("admin:blog_blogpost_page_save", args=[post.pk])
    page = sample_page()
    save_resp = client.post(
        page_save_url,
        data=json.dumps({"body_page": page, "expected_page_version": post.page_version}),
        content_type="application/json",
    )
    save_data = save_resp.json()
    record("PAGE_SAVE", "Page save persists", "PASS" if save_resp.status_code == 200 and save_data.get("ok") else "FAIL")
    post.refresh_from_db()
    record("PAGE_SAVE", "Reload retains content", "PASS" if "Naslov stranice" in (post.body_plaintext or "") else "FAIL")

    conflict_resp = client.post(
        page_save_url,
        data=json.dumps({"body_page": page, "expected_page_version": 999}),
        content_type="application/json",
    )
    record("PAGE_SAVE", "Version conflict returns 409", "PASS" if conflict_resp.status_code == 409 else "FAIL")

    bad_resp = client.post(
        page_save_url,
        data=json.dumps({"body_page": {"bad": True}}),
        content_type="application/json",
    )
    record("PAGE_SAVE", "Validation error returns 400", "PASS" if bad_resp.status_code == 400 else "FAIL")

    upload_url = reverse("admin:blog_blogpost_page_upload_image", args=[post.pk])
    upload_resp = client.post(upload_url, {"image": make_image()})
    upload_ok = upload_resp.status_code == 200 and upload_resp.json().get("ok")
    record("EDITOR", "Image upload API", "PASS" if upload_ok else "FAIL", upload_resp.content.decode()[:120])

    seo_payload = {
        "content_type_id": ct.pk,
        "object_id": post.pk,
        "article_title": post.title,
        "url_slug": post.slug,
        "excerpt": post.excerpt,
        "seo_title": post.title,
        "meta_description": "",
        "focus_keyword": "linkom",
        "body_plaintext": post.body_plaintext,
    }
    seo_endpoints = [
        "seo_keyword_analysis",
        "seo_readability_analysis",
        "seo_internal_linking_analysis",
        "seo_cornerstone_analysis",
        "seo_unified_score",
        "seo_image_seo_analysis",
        "seo_serp_preview",
        "seo_open_graph_preview",
        "seo_twitter_card_preview",
    ]
    for name in seo_endpoints:
        resp = client.post(
            reverse(f"admin:{name}"),
            data=json.dumps(seo_payload),
            content_type="application/json",
        )
        record("SEO", f"API {name}", "PASS" if resp.status_code == 200 else "FAIL", f"status={resp.status_code}")

    unified = client.post(
        reverse("admin:seo_unified_score"),
        data=json.dumps(seo_payload),
        content_type="application/json",
    ).json()
    record("SEO", "Word count in unified score", "PASS" if unified.get("word_count", 0) > 0 else "FAIL")

    post.title = "Objavljen audit"
    post.slug = "objavljen-audit"
    post.is_published = True
    post.publish_date = timezone.localdate()
    post.save()
    preview_resp = client.get(reverse("frontend:admin_preview_blog", args=[post.pk]))
    record("BLOG", "Staff preview", "PASS" if preview_resp.status_code == 200 else "FAIL")
    public_resp = client.get(post.get_absolute_url())
    record("BLOG", "Public blog detail", "PASS" if public_resp.status_code == 200 else "FAIL")

    for url_name in ("admin:index", "admin:blog_blogpost_changelist", "admin:layout_projektipage_changelist"):
        resp = client.get(reverse(url_name))
        record("ADMIN", f"Page {url_name}", "PASS" if resp.status_code == 200 else "FAIL")

    idx = html.find("data-seo-image-seo-analyzer")
    has_image_config = "seo_image_seo_analysis" in html and "data-object-id" in html
    record("SEO", "Image SEO analyzer present in editor HTML", "PASS" if idx >= 0 and has_image_config else "FAIL")

    fails = [r for r in RESULTS if r.status == "FAIL"]
    partials = [r for r in RESULTS if r.status == "PARTIAL"]
    print("\n=== SUMMARY ===")
    print(f"PASS: {sum(1 for r in RESULTS if r.status == 'PASS')}")
    print(f"PARTIAL: {len(partials)}")
    print(f"FAIL: {len(fails)}")
    if fails:
        print("\nFailures:")
        for f in fails:
            print(f"  - {f.area} / {f.feature}: {f.note}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
