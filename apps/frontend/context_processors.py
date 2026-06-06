from django.conf import settings


def contact_info(request):
    """Kontakt podaci dostupni u footeru i šablonima."""
    return {
        "contact_phone": getattr(settings, "CONTACT_PHONE", "+381 62 810 7037"),
        "contact_phone_display": getattr(
            settings, "CONTACT_PHONE_DISPLAY", "+381 62 810 7037"
        ),
        "contact_phone_2": getattr(settings, "CONTACT_PHONE_2", "+381 61 146 3318"),
        "contact_phone_2_display": getattr(
            settings, "CONTACT_PHONE_2_DISPLAY", "+381 61 146 3318"
        ),
        "contact_address": getattr(settings, "CONTACT_ADDRESS", "Srbija"),
    }
