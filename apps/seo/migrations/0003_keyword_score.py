from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0002_migrate_legacy_seo"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="keyword_score",
            field=models.PositiveSmallIntegerField(
                default=0,
                editable=False,
                verbose_name="Ocena ključne reči",
            ),
        ),
    ]
