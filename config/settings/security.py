"""
Security helpers — CSP, CSRF trusted origins (production / Cloudflare).
"""
from __future__ import annotations

from urllib.parse import urlparse


def build_csrf_trusted_origins(env, allowed_hosts: list[str], extra: list[str] | None = None) -> list[str]:
    origins: list[str] = list(extra or [])
    origins.extend(env.list("CSRF_TRUSTED_ORIGINS", default=[]))

    base_url = (env("SITE_BASE_URL", default="") or "").strip().rstrip("/")
    if base_url:
        origins.append(base_url)

    for host in allowed_hosts:
        host = (host or "").strip()
        if not host or host == "*" or host.startswith("."):
            continue
        if host.startswith("["):
            origins.append(f"https://{host}")
        else:
            origins.append(f"https://{host}")

    seen: set[str] = set()
    unique: list[str] = []
    for origin in origins:
        if origin and origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


def _origin_from_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    if not parsed.netloc:
        return ""
    scheme = parsed.scheme or "https"
    return f"{scheme}://{parsed.netloc}"


def build_csp_media_origins(
    *,
    media_url: str,
    custom_domain: str,
    extra: list[str] | None = None,
) -> list[str]:
    """Hostovi dozvoljeni u img-src / media-src (R2, Cloudflare CDN)."""
    origins: list[str] = list(extra or [])
    for value in (media_url, custom_domain):
        origin = _origin_from_url(value)
        if origin:
            origins.append(origin)
    seen: set[str] = set()
    unique: list[str] = []
    for origin in origins:
        if origin and origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


def build_content_security_policy(media_origins: list[str]) -> str:
    """CSP za javni sajt."""
    img_sources = ["'self'", "data:"] + media_origins
    img_src = " ".join(img_sources)

    directives = [
        "default-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
        "script-src 'self'",
        f"style-src 'self' 'unsafe-inline'",
        f"img-src {img_src}",
        "font-src 'self'",
        "connect-src 'self'",
        "frame-src 'none'",
        "upgrade-insecure-requests",
    ]
    return "; ".join(directives)
