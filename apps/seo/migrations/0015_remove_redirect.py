# Generated manually — remove Redirect model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0014_redirect"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Redirect",
        ),
    ]
