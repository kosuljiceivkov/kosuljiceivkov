from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0008_image_seo_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="robots_noarchive",
            field=models.BooleanField(
                default=False,
                help_text="Sprečava link ka keširanoj verziji stranice u Google-u.",
                verbose_name="Robots: noarchive",
            ),
        ),
        migrations.AddField(
            model_name="seometadata",
            name="robots_nosnippet",
            field=models.BooleanField(
                default=False,
                help_text="Sprečava prikaz tekstualnog isečka u rezultatima pretrage.",
                verbose_name="Robots: nosnippet",
            ),
        ),
        migrations.AddField(
            model_name="seometadata",
            name="robots_max_image_preview",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Podrazumevano (bez direktive)"),
                    ("large", "large — veliki pregled slike"),
                    ("standard", "standard — manji pregled"),
                    ("none", "none — bez pregleda slike"),
                ],
                default="",
                help_text="Kontroliše veličinu pregleda slike u rezultatima. Podrazumevano = bez eksplicitne direktive.",
                max_length=16,
                verbose_name="Robots: max-image-preview",
            ),
        ),
    ]
