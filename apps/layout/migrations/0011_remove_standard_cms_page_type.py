from django.db import migrations, models


def delete_standard_cms_pages(apps, schema_editor):
    CMSPage = apps.get_model("layout", "CMSPage")
    CMSPage.objects.filter(page_type="standard").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("layout", "0010_simplify_cms_page_help_text"),
    ]

    operations = [
        migrations.RunPython(delete_standard_cms_pages, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="cmspage",
            name="page_type",
            field=models.CharField(
                choices=[("projekti", "Projekti")],
                default="projekti",
                help_text="Javna stranica projekata koristi tip „Projekti” i rutu /projekti/.",
                max_length=32,
                verbose_name="Tip stranice",
            ),
        ),
    ]
