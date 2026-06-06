"""Generate PNG favicons from the site logo WebP."""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Generiše favicon.png i apple-touch-icon.png iz WebP logotipa "
        "(podrazumevano static/img/logo.webp)."
    )

    def handle(self, *args, **options):
        from pathlib import Path

        from PIL import Image

        base_dir = Path(settings.BASE_DIR)
        static_dir = base_dir / "static" / "img"
        logo_rel = getattr(settings, "SITE_FAVICON_WEBP", settings.SITE_ADMIN_BRAND_LOGO)
        logo_path = base_dir / "static" / logo_rel.replace("img/", "img/")

        if not logo_path.is_file():
            logo_path = static_dir / "logo.webp"
        if not logo_path.is_file():
            self.stderr.write(
                self.style.ERROR(
                    "Postavite static/img/logo.webp pa pokrenite ponovo."
                )
            )
            return

        with Image.open(logo_path) as im:
            im = im.convert("RGBA")
            favicon = im.resize((32, 32), Image.Resampling.LANCZOS)
            apple = im.resize((180, 180), Image.Resampling.LANCZOS)
            favicon.save(static_dir / "favicon.png", format="PNG")
            apple.save(static_dir / "apple-touch-icon.png", format="PNG")

        self.stdout.write(self.style.SUCCESS("Favicon fajlovi su generisani u static/img/."))
