from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0011_alter_seometadata_og_image_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="robots_max_snippet",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Podrazumevano (bez direktive)"),
                    ("-1", "-1 — bez ograničenja isečka"),
                    ("0", "0 — bez isečka u rezultatima"),
                ],
                default="",
                help_text="Kontroliše dužinu tekstualnog isečka u rezultatima. Podrazumevano = bez eksplicitne direktive.",
                max_length=16,
                verbose_name="Robots: max-snippet",
            ),
        ),
        migrations.AlterField(
            model_name="seometadata",
            name="focus_keyword",
            field=models.CharField(
                blank=True,
                help_text="Samo za CMS analizu i preporuke — ne izlazi u HTML meta tagove.",
                max_length=100,
                verbose_name="Fokus ključna reč",
            ),
        ),
        migrations.AlterField(
            model_name="seometadata",
            name="secondary_keywords",
            field=models.CharField(
                blank=True,
                help_text="Odvojite zarezom, npr. cement, fasada, temelj. Samo za internu analizu — ne izlaze u HTML.",
                max_length=255,
                verbose_name="Sekundarne ključne reči",
            ),
        ),
    ]
