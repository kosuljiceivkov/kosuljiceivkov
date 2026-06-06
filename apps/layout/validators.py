"""Validatori za page builder — bezbednost i format polja."""

import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

HEX_COLOR_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
RGB_COLOR_RE = re.compile(
    r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$"
)
RGBA_COLOR_RE = re.compile(
    r"^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*"
    r"(0(?:\.\d+)?|1(?:\.0+)?)\s*\)$"
)

ALLOWED_VIDEO_NETLOCS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
        "www.youtu.be",
        "vimeo.com",
        "www.vimeo.com",
        "player.vimeo.com",
    }
)


def validate_css_color(value):
    """Dozvoljava prazno, HEX, rgb() ili rgba()."""
    if not value or not str(value).strip():
        return

    value = str(value).strip()
    if HEX_COLOR_RE.match(value):
        return

    rgb_match = RGB_COLOR_RE.match(value)
    if rgb_match:
        if all(0 <= int(part) <= 255 for part in rgb_match.groups()):
            return
        raise ValidationError(
            _("RGB vrednosti moraju biti između 0 i 255."),
            code="invalid_rgb",
        )

    rgba_match = RGBA_COLOR_RE.match(value)
    if rgba_match:
        r, g, b, a = rgba_match.groups()
        if not all(0 <= int(channel) <= 255 for channel in (r, g, b)):
            raise ValidationError(
                _("RGBA vrednosti moraju biti između 0 i 255."),
                code="invalid_rgba",
            )
        if not (0 <= float(a) <= 1):
            raise ValidationError(
                _("RGBA alpha vrednost mora biti između 0 i 1."),
                code="invalid_rgba_alpha",
            )
        return

    raise ValidationError(
        _(
            "Unesite validnu boju: HEX (#rrggbb), rgb(r,g,b) ili rgba(r,g,b,a). "
            "Inline CSS i druge vrednosti nisu dozvoljene."
        ),
        code="invalid_css_color",
    )


def validate_video_embed_url(value):
    """Dozvoljava samo YouTube i Vimeo embed URL adrese."""
    if not value or not str(value).strip():
        return

    parsed = urlparse(str(value).strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError(
            _("Embed link mora počinjati sa http:// ili https://."),
            code="invalid_video_scheme",
        )

    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host_normalized = host
    else:
        host_normalized = host

    if host_normalized not in ALLOWED_VIDEO_NETLOCS:
        raise ValidationError(
            _(
                "Dozvoljeni su samo YouTube i Vimeo embed linkovi "
                "(youtube.com, youtu.be, vimeo.com)."
            ),
            code="invalid_video_host",
        )
