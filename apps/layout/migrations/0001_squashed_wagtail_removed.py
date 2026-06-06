from django.db import migrations


class Migration(migrations.Migration):

    replaces = [
        ("layout", "0001_initial"),
        ("layout", "0002_remove_flexpage"),
    ]

    initial = True

    dependencies = [
        ("blog", "0001_squashed_wagtail_removed"),
    ]

    operations = []
