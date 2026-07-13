from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("layout", "0015_remove_legacy_builder_models"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cmspage",
            name="authoring_mode",
        ),
    ]
