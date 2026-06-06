"""
Security and cache middleware — Cloudflare + Render compatible.
"""
from __future__ import annotations

from django.conf import settings
from django.utils.cache import patch_cache_control
from django.utils.deprecation import MiddlewareMixin

_ADMIN_PREFIXES = ("/admin", "/django-admin", "/documents")
_SKIP_CACHE_PREFIXES = _ADMIN_PREFIXES


def _is_admin_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _ADMIN_PREFIXES)


def _should_apply_public_cache(path: str, method: str) -> bool:
    if method != "GET":
        return False
    if _is_admin_path(path) or any(path.startswith(p) for p in _SKIP_CACHE_PREFIXES):
        return False
    if path.startswith("/static/") or path.startswith("/media/"):
        return False
    return True


class SecurityHeadersMiddleware(MiddlewareMixin):
    """CSP, Permissions-Policy i XSS zaštita na javnom sajtu."""

    def process_response(self, request, response):
        if _is_admin_path(request.path):
            return response

        if getattr(settings, "CONTENT_SECURITY_POLICY", None):
            response["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY

        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-XSS-Protection", "1; mode=block")
        response.setdefault("Referrer-Policy", getattr(settings, "SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin"))
        response.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
        )
        return response


class PublicCacheHeadersMiddleware(MiddlewareMixin):
    """
    Cache-Control za HTML stranice — Cloudflare edge cache.
    Statički fajlovi: WhiteNoise; mediji: R2 object metadata.
    """

    def process_response(self, request, response):
        if not _should_apply_public_cache(request.path, request.method):
            return response

        if response.status_code != 200:
            return response

        if "Cache-Control" in response:
            return response

        max_age = getattr(settings, "PUBLIC_HTML_CACHE_MAX_AGE", 300)
        s_maxage = getattr(settings, "PUBLIC_HTML_S_MAXAGE", 600)

        patch_cache_control(
            response,
            public=True,
            max_age=max_age,
            s_maxage=s_maxage,
            stale_while_revalidate=60,
        )
        response["Vary"] = "Accept-Encoding"
        if getattr(settings, "USE_CLOUDFLARE_PROXY", False):
            response["CDN-Cache-Control"] = f"public, max-age={s_maxage}"
        return response
