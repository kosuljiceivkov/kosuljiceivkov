from django.apps import AppConfig


class LayoutConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.layout"
    verbose_name = "Projekti"

    def ready(self):
        from . import signals  # noqa: F401
