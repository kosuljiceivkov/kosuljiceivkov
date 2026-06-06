"""
Production settings — PostgreSQL, Cloudflare R2 media, security hardening.
"""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .media import build_r2_media_storages, get_media_url_for_r2
from .security import (
    build_content_security_policy,
    build_csp_media_origins,
    build_csrf_trusted_origins,
)

DEBUG = False

USE_R2_STORAGE = env.bool("USE_R2_STORAGE", default=True)  # noqa: F405
REQUIRE_R2_CONFIG = env.bool("REQUIRE_R2_CONFIG", default=True)  # noqa: F405

# ---------------------------------------------------------------------------
# PostgreSQL (Render DATABASE_URL) — ista šema migracija kao lokalni SQLite
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL"),  # noqa: F405
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)  # noqa: F405
DATABASES["default"]["OPTIONS"] = {
    "sslmode": env("DB_SSLMODE", default="require"),  # noqa: F405
}

# ---------------------------------------------------------------------------
# Cloudflare R2 media storage
# ---------------------------------------------------------------------------
_required_r2 = {
    "R2_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,  # noqa: F405
    "R2_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,  # noqa: F405
    "R2_BUCKET_NAME": AWS_STORAGE_BUCKET_NAME,  # noqa: F405
    "R2_ENDPOINT_URL": AWS_S3_ENDPOINT_URL,  # noqa: F405
}
_missing = [name for name, val in _required_r2.items() if not val]
if USE_R2_STORAGE and _missing and REQUIRE_R2_CONFIG:
    raise ImproperlyConfigured(
        "Cloudflare R2 is enabled (USE_R2_STORAGE=True) but missing: "
        + ", ".join(_missing)
        + ". Set variables on Render or REQUIRE_R2_CONFIG=False for build-only."
    )

STORAGES = {  # noqa: F405
    **build_r2_media_storages(),
    "staticfiles": STORAGES["staticfiles"],  # noqa: F405
}

MEDIA_URL = (
    env("R2_MEDIA_URL", default="")  # noqa: F405
    or env("MEDIA_URL", default=get_media_url_for_r2())  # noqa: F405
)

# ---------------------------------------------------------------------------
# Static files (WhiteNoise) — hashed assets, long cache
# ---------------------------------------------------------------------------
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp", "zip", "gz", "br")

# ---------------------------------------------------------------------------
# Security — HSTS, cookies, CSRF, XSS, CSP
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", default=True)  # noqa: F405
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_USE_SESSIONS = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)  # noqa: F405

CSRF_TRUSTED_ORIGINS = build_csrf_trusted_origins(env, ALLOWED_HOSTS)  # noqa: F405

_csp_media = build_csp_media_origins(
    media_url=MEDIA_URL,
    custom_domain=AWS_S3_CUSTOM_DOMAIN,  # noqa: F405
    extra=env.list("CSP_EXTRA_MEDIA_ORIGINS", default=[]),  # noqa: F405
)
CONTENT_SECURITY_POLICY = build_content_security_policy(_csp_media)

# Cloudflare proxy (orange cloud) — optional CDN-Cache-Control headers
USE_CLOUDFLARE_PROXY = env.bool("USE_CLOUDFLARE_PROXY", default=False)  # noqa: F405
PUBLIC_HTML_CACHE_MAX_AGE = env.int("PUBLIC_HTML_CACHE_MAX_AGE", default=300)  # noqa: F405
PUBLIC_HTML_S_MAXAGE = env.int("PUBLIC_HTML_S_MAXAGE", default=600)  # noqa: F405

MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
_security_index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1
MIDDLEWARE.insert(_security_index, "apps.core.middleware.SecurityHeadersMiddleware")
MIDDLEWARE.append("apps.core.middleware.PublicCacheHeadersMiddleware")

LOGGING["root"]["level"] = "WARNING"  # noqa: F405
