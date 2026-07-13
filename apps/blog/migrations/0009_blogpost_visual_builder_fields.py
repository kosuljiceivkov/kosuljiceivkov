# Generated manually — visual builder fields for BlogPost.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0008_blogpost_document_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="body_page",
            field=models.JSONField(
                blank=True,
                help_text="Interni iv_page_v1 format za visual builder.",
                null=True,
                verbose_name="Sadržaj (page JSON)",
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="page_version",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Raste monotono pri svakoj promeni page sadržaja (autosave, konflikti, revizije).",
                verbose_name="Verzija stranice",
            ),
        ),
        migrations.AlterField(
            model_name="blogpost",
            name="authoring_mode",
            field=models.CharField(
                choices=[
                    ("legacy_builder", "Stari page builder"),
                    ("document", "Document editor"),
                    ("visual_builder", "Visual builder"),
                ],
                default="legacy_builder",
                help_text="Postojeće objave zadržavaju stari builder dok se ne prebace na document editor.",
                max_length=20,
                verbose_name="Način uređivanja",
            ),
        ),
    ]
