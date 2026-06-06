from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0006_schema_type_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="seometadata",
            name="internal_linking_score",
            field=models.PositiveSmallIntegerField(
                default=0,
                editable=False,
                verbose_name="Ocena internih linkova",
            ),
        ),
    ]
