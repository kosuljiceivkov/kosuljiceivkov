from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Osnovno"

    def ready(self):
        from . import admin  # noqa: F401
        from .media_signals import connect_media_cleanup_signals

        connect_media_cleanup_signals()

