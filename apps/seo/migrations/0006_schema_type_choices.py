from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0005_twitter_card_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="seometadata",
            name="schema_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Automatski (preporučeno)"),
                    ("Article", "Article"),
                    ("BlogPosting", "BlogPosting"),
                    ("FAQPage", "FAQPage"),
                    ("WebPage", "WebPage"),
                    ("Person", "Person"),
                    ("Organization", "Organization"),
                    ("Service", "Service"),
                    ("ItemList", "ItemList"),
                    ("LocalBusiness", "LocalBusiness"),
                ],
                default="",
                help_text="Primarni JSON-LD tip: BlogPosting za blog, WebPage za CMS, FAQPage ako imate FAQ u builderu, Person/Organization za profile.",
                max_length=32,
                verbose_name="Schema.org tip",
            ),
        ),
    ]
