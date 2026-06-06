"""
Local development settings — SQLite, debug enabled, MEDIA_ROOT.
"""
from .base import *  # noqa: F403
from .media import build_local_media_storages

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

USE_R2_STORAGE = False

# SQLite for local development (no PostgreSQL required)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Lokalni HTTP — bez obaveznog HTTPS na kolačićima
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Lokalni mediji — podfolderi u MEDIA_ROOT
_media_storages = build_local_media_storages(MEDIA_ROOT, MEDIA_URL)  # noqa: F405
STORAGES = {  # noqa: F405
    **_media_storages,
    "staticfiles": STORAGES["staticfiles"],  # noqa: F405
}
