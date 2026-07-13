from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0012_robots_max_snippet"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="include_in_sitemap",
            field=models.BooleanField(
                default=True,
                help_text="Isključite za stranice koje ne želite u sitemap.xml (npr. thank-you, landing bez SEO vrednosti).",
                verbose_name="Uključi u sitemap",
            ),
        ),
    ]
