from django.db import migrations, models


def migrate_legacy_authoring_modes(apps, schema_editor):
    CMSPage = apps.get_model("layout", "CMSPage")
    CMSPage.objects.filter(authoring_mode="legacy_builder").update(
        authoring_mode="visual_builder"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("layout", "0014_cmspage_visual_builder_fields"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_authoring_modes, migrations.RunPython.noop),
        migrations.DeleteModel(name="CarouselItem"),
        migrations.DeleteModel(name="Carousel"),
        migrations.DeleteModel(name="BlockGalleryImage"),
        migrations.DeleteModel(name="Block"),
        migrations.DeleteModel(name="Column"),
        migrations.DeleteModel(name="Row"),
        migrations.DeleteModel(name="Section"),
        migrations.AlterField(
            model_name="cmspage",
            name="authoring_mode",
            field=models.CharField(
                choices=[("visual_builder", "Visual builder")],
                default="visual_builder",
                max_length=20,
                verbose_name="Način uređivanja",
            ),
        ),
    ]
