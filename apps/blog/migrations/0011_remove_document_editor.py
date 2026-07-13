from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0010_remove_legacy_builder"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="blogpost",
            name="body_document",
        ),
        migrations.RemoveField(
            model_name="blogpost",
            name="body_format",
        ),
        migrations.RemoveField(
            model_name="blogpost",
            name="document_version",
        ),
        migrations.RemoveField(
            model_name="blogpost",
            name="authoring_mode",
        ),
    ]
