import re

from django import template

register = template.Library()


@register.filter
def phone_uri(value):
    """tel: link — zadržava + i cifre."""
    if not value:
        return ""
    cleaned = re.sub(r"[^\d+]", "", str(value))
    return cleaned
