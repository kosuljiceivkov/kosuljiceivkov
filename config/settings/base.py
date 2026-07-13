"""
Shared Django settings for all environments.
"""
from pathlib import Path

import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env if present (local development)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = []

LOCAL_APPS = [
    "apps.core",
    "apps.seo",
    "apps.blog",
    "apps.layout",
    "apps.page",
    "apps.frontend",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.seo.middleware.RedirectFallbackMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.frontend.context_processors.contact_info",
                "apps.seo.context_processors.seo_site",
                "apps.core.context_processors.site_branding",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database — overridden in local.py / production.py
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Localization — Serbian (Latin script) only
LANGUAGE_CODE = "sr-latn"
TIME_ZONE = "Europe/Belgrade"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("sr-latn", "Srpski (latinica)"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# Site branding (public site + Django admin)
SITE_ADMIN_BRAND_NAME = "Cementne košuljice Ivkov (admin)"
SITE_ADMIN_BRAND_LOGO = "img/logo.webp"
SITE_FAVICON_WEBP = "img/logo.webp"
SITE_FAVICON_PNG = "img/favicon.png"
SITE_FAVICON_APPLE = "img/apple-touch-icon.png"
SITE_BASE_URL = env("SITE_BASE_URL", default="http://localhost:8000")

# Static & media files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": BASE_DIR / "media",
            "base_url": "/media/",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Media storage mode (overridden in local.py / production.py)
USE_R2_STORAGE = env.bool("USE_R2_STORAGE", default=False)


def _env_r2_or_aws(r2_key: str, aws_key: str, *, default: str = "") -> str:
    """R2_* env vars (preferred) with legacy AWS_* fallback for django-storages."""
    return env(r2_key, default="") or env(aws_key, default=default)


# Cloudflare R2 — R2_* on Render; mapped to django-storages AWS_* settings internally
AWS_ACCESS_KEY_ID = _env_r2_or_aws("R2_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = _env_r2_or_aws("R2_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = _env_r2_or_aws("R2_BUCKET_NAME", "AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = _env_r2_or_aws("R2_ENDPOINT_URL", "AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = _env_r2_or_aws("R2_REGION_NAME", "AWS_S3_REGION_NAME", default="auto") or "auto"
AWS_S3_CUSTOM_DOMAIN = _env_r2_or_aws("R2_CUSTOM_DOMAIN", "AWS_S3_CUSTOM_DOMAIN")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cookies and CSRF (hardened in production.py)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

CONTACT_PHONE = env("CONTACT_PHONE", default="+381 62 810 7037")
CONTACT_PHONE_DISPLAY = env("CONTACT_PHONE_DISPLAY", default="+381 62 810 7037")
CONTACT_PHONE_2 = env("CONTACT_PHONE_2", default="+381 61 146 3318")
CONTACT_PHONE_2_DISPLAY = env("CONTACT_PHONE_2_DISPLAY", default="+381 61 146 3318")
CONTACT_ADDRESS = env(
    "CONTACT_ADDRESS",
    default="Naše usluge pružamo na teritoriji cele Srbije.",
)

# SEO defaults (when page has no seo_object)
SEO_SITE_NAME = "Cementne košuljice Ivkov"
SEO_DEFAULT_TITLE = env(
    "SEO_DEFAULT_TITLE",
    default="Cementne košuljice Ivkov — Izrada i ugradnja košuljica",
)
SEO_DEFAULT_DESCRIPTION = env(
    "SEO_DEFAULT_DESCRIPTION",
    default="Izrada i ugradnja cementnih i betonskih košuljica. Profesionalna usluga širom Srbije.",
)
SEO_DEFAULT_KEYWORDS = env(
    "SEO_DEFAULT_KEYWORDS",
    default="cementne košuljice, betonske košuljice, terase, stepeništa",
)
SEO_DEFAULT_OG_IMAGE_URL = env(
    "SEO_DEFAULT_OG_IMAGE_URL",
    default="/static/img/cementne-kosuljice6.webp",
)
SEO_DISALLOW_ALL = env.bool("SEO_DISALLOW_ALL", default=False)
SEO_BLOG_AUTHOR_NAME = env(
    "SEO_BLOG_AUTHOR_NAME",
    default="Cementne košuljice Ivkov",
)
SEO_BLOG_AUTHOR_TYPE = env("SEO_BLOG_AUTHOR_TYPE", default="Organization")
SEO_PERSON_NAME = env("SEO_PERSON_NAME", default="")
SEO_PERSON_URL = env("SEO_PERSON_URL", default="")
SEO_PERSON_IMAGE = env("SEO_PERSON_IMAGE", default="")
SEO_PERSON_JOB_TITLE = env("SEO_PERSON_JOB_TITLE", default="")
SEO_ORGANIZATION_EMAIL = env("SEO_ORGANIZATION_EMAIL", default="")
SEO_ORGANIZATION_LOGO = env(
    "SEO_ORGANIZATION_LOGO",
    default="img/logo.webp",
)
SEO_ORGANIZATION_COUNTRY = env("SEO_ORGANIZATION_COUNTRY", default="RS")

BREADCRUMB_HOME_TITLE = env("BREADCRUMB_HOME_TITLE", default="Početna")
BREADCRUMB_BLOG_TITLE = env("BREADCRUMB_BLOG_TITLE", default="Blog")

# Canonical URL management
SEO_CANONICAL_DEFAULT_LANGUAGE = env(
    "SEO_CANONICAL_DEFAULT_LANGUAGE",
    default=LANGUAGE_CODE,
)
SEO_CANONICAL_PAGINATION_PARAM = env("SEO_CANONICAL_PAGINATION_PARAM", default="page")
SEO_CANONICAL_LANGUAGE_PREFIX = env.bool("SEO_CANONICAL_LANGUAGE_PREFIX", default=False)
SEO_HREFLANG_ENABLED = env.bool("SEO_HREFLANG_ENABLED", default=False)

# Keš — page builder fragmenti i verzije
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cementnekosuljiceivkov-default",
    },
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
