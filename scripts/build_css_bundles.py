#!/usr/bin/env python3
"""
Spaja CSS fajlove u bundle fajlove (bez @import lanca — manje render-blocking zahteva).

Pokretanje: python scripts/build_css_bundles.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "static" / "css"
OUT = CSS / "bundles"

CORE_FILES = [
    "fonts.css",
    "variables.css",
    "typography.css",
    "utilities.css",
    "navigation.css",
    "global.css",
]

DEFER_FILES = [
    "contact.css",
    "scroll-fab.css",
    "components.css",
]

CAROUSEL_FILES = [
    "carousel-shared.css",
    "project-showcase-carousel.css",
]


def minify_css(text: str) -> str:
    """Lightweight minification — uklanja komentare i suvišan whitespace."""
    text = re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}:;,>+~])\s*", r"\1", text)
    return text.strip()


def concat(files: list[str], banner: str) -> str:
    parts = [f"/* {banner} — generated; do not edit by hand */\n"]
    for name in files:
        path = CSS / name
        parts.append(f"\n/* --- {name} --- */\n")
        parts.append(path.read_text(encoding="utf-8"))
        if not parts[-1].endswith("\n"):
            parts.append("\n")
    return minify_css("".join(parts))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    core = concat(CORE_FILES, "site-core bundle")
    defer = concat(DEFER_FILES, "site-defer bundle")
    carousel = concat(CAROUSEL_FILES, "site-carousel bundle")
    (OUT / "site-core.css").write_text(core, encoding="utf-8")
    (OUT / "site-defer.css").write_text(defer, encoding="utf-8")
    (OUT / "site-carousel.css").write_text(carousel, encoding="utf-8")
    print(f"Wrote {OUT / 'site-core.css'} ({len(core):,} bytes, {len(CORE_FILES)} files)")
    print(f"Wrote {OUT / 'site-defer.css'} ({len(defer):,} bytes, {len(DEFER_FILES)} files)")
    print(f"Wrote {OUT / 'site-carousel.css'} ({len(carousel):,} bytes, {len(CAROUSEL_FILES)} files)")


if __name__ == "__main__":
    main()
