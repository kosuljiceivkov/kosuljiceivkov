from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Osnovno"

    def ready(self):
        from django.conf import settings
        from django.contrib import admin as django_admin

        from . import admin  # noqa: F401
        from . import signals  # noqa: F401
        from .storage_aliases import resolve_filefield_storage_aliases

        resolve_filefield_storage_aliases()

        brand_name = getattr(
            settings,
            "SITE_ADMIN_BRAND_NAME",
            "Cementne košuljice Ivkov (admin)",
        )
        django_admin.site.site_header = brand_name
        django_admin.site.site_title = brand_name

