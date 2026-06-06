from django.db import migrations


class Migration(migrations.Migration):

    replaces = [
        ("blog", "0001_initial"),
        ("blog", "0002_blogcategory_remove_blogpage_page_ptr_blogpost_and_more"),
        ("blog", "0003_blogpost_canonical_url_blogpost_focus_keyword_and_more"),
        ("blog", "0004_add_two_column_block"),
        ("blog", "0005_add_columns_block"),
        ("blog", "0006_remove_snippet_models"),
        ("blog", "0007_initial"),
        ("blog", "0008_remove_wagtail_pages"),
    ]

    initial = True

    dependencies = []

    operations = []
