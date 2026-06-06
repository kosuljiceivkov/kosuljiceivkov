from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0004_open_graph_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="twitter_card",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Automatski (preporučeno)"),
                    ("summary", "summary"),
                    ("summary_large_image", "summary_large_image"),
                ],
                default="",
                help_text="Automatski: summary_large_image ako postoji slika, inače summary.",
                max_length=32,
                verbose_name="Twitter Card tip",
            ),
        ),
        migrations.AlterField(
            model_name="seometadata",
            name="twitter_image",
            field=models.ImageField(
                blank=True,
                help_text="Preporučeno: 1200×630 px za summary_large_image. Prazno = Open Graph slika ili istaknuta slika.",
                storage="blog_images",
                upload_to="seo/twitter/%Y/%m/",
                verbose_name="Twitter slika",
            ),
        ),
    ]
