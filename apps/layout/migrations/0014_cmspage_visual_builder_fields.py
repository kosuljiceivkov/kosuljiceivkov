from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("layout", "0013_alter_block_image_alter_block_video_file_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cmspage",
            name="authoring_mode",
            field=models.CharField(
                choices=[
                    ("legacy_builder", "Stari builder"),
                    ("visual_builder", "Visual builder"),
                ],
                default="legacy_builder",
                help_text="Postojeći sadržaj zadržava stari builder dok se ne prebaci na visual builder.",
                max_length=20,
                verbose_name="Način uređivanja",
            ),
        ),
        migrations.AddField(
            model_name="cmspage",
            name="body_format",
            field=models.CharField(
                blank=True,
                default="iv_page_v1",
                help_text="Verzija internog page formata, npr. iv_page_v1.",
                max_length=32,
                verbose_name="Format sadržaja",
            ),
        ),
        migrations.AddField(
            model_name="cmspage",
            name="body_page",
            field=models.JSONField(
                blank=True,
                help_text="Interni iv_page_v1 format za visual builder.",
                null=True,
                verbose_name="Sadržaj (page JSON)",
            ),
        ),
        migrations.AddField(
            model_name="cmspage",
            name="body_plaintext",
            field=models.TextField(
                blank=True,
                editable=False,
                help_text="Automatski izvučen iz page JSON-a za pretragu i SEO.",
                verbose_name="Sadržaj (običan tekst)",
            ),
        ),
        migrations.AddField(
            model_name="cmspage",
            name="page_version",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Raste monotono pri svakoj promeni page sadržaja (autosave, konflikti).",
                verbose_name="Verzija stranice",
            ),
        ),
    ]
