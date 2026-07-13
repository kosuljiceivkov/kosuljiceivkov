# Generated manually for Milestone 1 — blog document fields.

import apps.core.storage_aliases
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0006_alter_blogpost_featured_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="authoring_mode",
            field=models.CharField(
                choices=[
                    ("legacy_builder", "Stari page builder"),
                    ("document", "Document editor"),
                ],
                default="legacy_builder",
                help_text="Postojeće objave zadržavaju stari builder dok se ne prebace na document editor.",
                max_length=20,
                verbose_name="Način uređivanja",
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="body_document",
            field=models.JSONField(
                blank=True,
                help_text="Interni iv_document_v1 format — nezavisan od editor biblioteke.",
                null=True,
                verbose_name="Sadržaj (document JSON)",
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="body_plaintext",
            field=models.TextField(
                blank=True,
                editable=False,
                help_text="Automatski izvučen iz document JSON-a za pretragu i SEO.",
                verbose_name="Sadržaj (običan tekst)",
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="body_format",
            field=models.CharField(
                blank=True,
                default="iv_document_v1",
                help_text="Verzija internog document formata, npr. iv_document_v1.",
                max_length=32,
                verbose_name="Format sadržaja",
            ),
        ),
        migrations.AlterField(
            model_name="blogpost",
            name="featured_image",
            field=models.ImageField(
                blank=True,
                help_text="Prikazuje se na kartici u listi bloga i u zaglavlju članka.",
                storage=apps.core.storage_aliases.blog_images_storage,
                upload_to="blog/featured/%Y/%m/",
                verbose_name="Istaknuta slika",
            ),
        ),
    ]
