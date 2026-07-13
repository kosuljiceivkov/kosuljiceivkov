from django.db import migrations, models


def migrate_legacy_authoring_modes(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    BlogPost.objects.filter(authoring_mode="legacy_builder").update(
        authoring_mode="visual_builder"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0009_blogpost_visual_builder_fields"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_authoring_modes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="blogpost",
            name="authoring_mode",
            field=models.CharField(
                choices=[
                    ("document", "Document editor"),
                    ("visual_builder", "Visual builder"),
                ],
                default="visual_builder",
                help_text="Visual builder je podrazumevani način uređivanja novih objava.",
                max_length=20,
                verbose_name="Način uređivanja",
            ),
        ),
    ]
