"""
Test settings — brzi testovi sa lokalnim filesystem storage-om.
"""
import os

os.environ.setdefault("SECRET_KEY", "django-test-secret-key-not-for-production")

from .base import *  # noqa: F403
from .media import build_local_media_storages

DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

USE_R2_STORAGE = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

MEDIA_ROOT = BASE_DIR / "test_media"  # noqa: F405

_media_storages = build_local_media_storages(MEDIA_ROOT, MEDIA_URL)  # noqa: F405
STORAGES = {  # noqa: F405
    **_media_storages,
    "staticfiles": STORAGES["staticfiles"],  # noqa: F405
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()
