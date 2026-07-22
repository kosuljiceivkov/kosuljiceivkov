# Generated manually — featured images live under blog/images/featured/.

from django.db import migrations, models

import apps.core.storage_aliases


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0016_alter_blogpost_featured_image_upload_to"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogpost",
            name="featured_image",
            field=models.ImageField(
                blank=True,
                help_text="Prikazuje se na kartici u listi bloga i u zaglavlju članka.",
                storage=apps.core.storage_aliases.blog_images_storage,
                upload_to="featured/%Y/%m/",
                verbose_name="Istaknuta slika",
            ),
        ),
    ]
