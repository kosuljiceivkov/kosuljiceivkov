from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0003_keyword_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="og_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Automatski (preporučeno)"),
                    ("website", "website"),
                    ("article", "article"),
                    ("product", "product"),
                    ("profile", "profile"),
                    ("video.other", "video.other"),
                ],
                default="",
                help_text="Automatski: article za blog, website za CMS stranice.",
                max_length=20,
                verbose_name="Open Graph tip",
            ),
        ),
        migrations.AddField(
            model_name="seometadata",
            name="og_url",
            field=models.URLField(
                blank=True,
                help_text="Ručni override za og:url. Prazno = kanonski URL.",
                verbose_name="Open Graph URL",
            ),
        ),
    ]
