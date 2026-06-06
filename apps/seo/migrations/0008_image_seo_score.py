from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0007_internal_linking_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="image_seo_score",
            field=models.PositiveSmallIntegerField(
                default=0,
                editable=False,
                verbose_name="Ocena slika",
            ),
        ),
    ]
