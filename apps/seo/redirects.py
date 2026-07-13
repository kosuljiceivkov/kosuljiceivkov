"""Automatska preusmerenja pri promeni slug-a."""

from __future__ import annotations

from apps.seo.models import Redirect, RedirectType, normalize_redirect_path


def create_redirect_for_url_change(old_url: str, new_url: str, *, note: str = "") -> Redirect | None:
    """
    Kreira 301 preusmerenje sa stare na novu putanju.

    - Ažurira postojeće preusmerenja koja su vodila na staru putanju (bez lanaca).
    - Briše preusmerenje čija je stara putanja jednaka novoj (stranica ponovo postoji).
    - Vraća None ako su putanje iste ili nevalidne.
    """
    old_path = normalize_redirect_path(old_url)
    new_path = normalize_redirect_path(new_url)

    if not old_path or not new_path or old_path == new_path:
        return None

    # Stranica sada živi na new_path — preusmerenje sa te putanje više nema smisla.
    Redirect.objects.filter(old_path=new_path).delete()

    # Izbegni lance: A→B pa B→C postaje A→C.
    Redirect.objects.filter(new_path=old_path).update(new_path=new_path)

    redirect, _ = Redirect.objects.update_or_create(
        old_path=old_path,
        defaults={
            "new_path": new_path,
            "redirect_type": RedirectType.PERMANENT,
            "is_active": True,
            "note": note[:255],
        },
    )
    return redirect
