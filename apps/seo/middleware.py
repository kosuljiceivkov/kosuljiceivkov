"""Redirect middleware — 301/302/410 fallback kada bi stranica vratila 404."""

from __future__ import annotations

from django.http import HttpResponseGone, HttpResponsePermanentRedirect, HttpResponseRedirect

from apps.seo.models import Redirect, RedirectType, normalize_redirect_path


class RedirectFallbackMiddleware:
    """
    Proverava tabelu preusmerenja samo za odgovore koji bi bili 404.

    Redosled rešavanja putanje: tačna putanja, zatim varijanta bez/sa
    završnom kosom crtom (normalizacija pokriva obe).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code != 404:
            return response

        path = normalize_redirect_path(request.path_info)
        if not path:
            return response

        redirect = (
            Redirect.objects.filter(old_path=path, is_active=True)
            .only("new_path", "redirect_type")
            .first()
        )
        if redirect is None:
            return response

        if redirect.redirect_type == RedirectType.GONE:
            return HttpResponseGone()

        if not redirect.new_path:
            return response

        if redirect.redirect_type == RedirectType.TEMPORARY:
            return HttpResponseRedirect(redirect.new_path)
        return HttpResponsePermanentRedirect(redirect.new_path)
