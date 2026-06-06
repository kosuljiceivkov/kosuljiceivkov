"""Kopira legacy meta polja sa BlogPost i CMSPage u SeoMetadata."""

from django.db import migrations


def migrate_legacy_seo_fields(apps, schema_editor):
    SeoMetadata = apps.get_model("seo", "SeoMetadata")
    ContentType = apps.get_model("contenttypes", "ContentType")
    BlogPost = apps.get_model("blog", "BlogPost")
    CMSPage = apps.get_model("layout", "CMSPage")

    blog_ct = ContentType.objects.get(app_label="blog", model="blogpost")
    cms_ct = ContentType.objects.get(app_label="layout", model="cmspage")

    seo_rows = []
    for post in BlogPost.objects.all().iterator():
        if not any((post.meta_title, post.meta_description, post.canonical_url)):
            continue
        seo_rows.append(
            SeoMetadata(
                content_type=blog_ct,
                object_id=post.pk,
                seo_title=post.meta_title or "",
                meta_description=post.meta_description or "",
                canonical_url=post.canonical_url or "",
            )
        )

    for page in CMSPage.objects.all().iterator():
        if not any((page.meta_title, page.meta_description, page.canonical_url)):
            continue
        seo_rows.append(
            SeoMetadata(
                content_type=cms_ct,
                object_id=page.pk,
                seo_title=page.meta_title or "",
                meta_description=page.meta_description or "",
                canonical_url=page.canonical_url or "",
            )
        )

    if seo_rows:
        SeoMetadata.objects.bulk_create(seo_rows, ignore_conflicts=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0001_initial"),
        ("blog", "0003_blogpost_canonical_url_alter_blogpost_excerpt_and_more"),
        ("layout", "0011_remove_standard_cms_page_type"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_seo_fields, noop_reverse),
    ]
