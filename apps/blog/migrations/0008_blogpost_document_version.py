# Generated manually — document_version for optimistic locking / autosave.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0007_blogpost_document_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="document_version",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Raste monotono pri svakoj promeni document sadržaja (autosave, konflikti, revizije).",
                verbose_name="Verzija dokumenta",
            ),
        ),
    ]
