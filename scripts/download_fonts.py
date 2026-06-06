#!/usr/bin/env python3
"""Preuzima latin-ext woff2 fontove sa Google Fonts CDN-a."""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "fonts"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;600;700&family=Barlow:wght@600;700&display=swap"
)

TARGETS = {
    ("Inter", "400"): "inter-latin-ext-400.woff2",
    ("Inter", "600"): "inter-latin-ext-600.woff2",
    ("Inter", "700"): "inter-latin-ext-700.woff2",
    ("Barlow", "600"): "barlow-latin-ext-600.woff2",
    ("Barlow", "700"): "barlow-latin-ext-700.woff2",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(CSS_URL, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    blocks = re.findall(r"/\* ([^*]+) \*/\s*@font-face\s*\{([^}]+)\}", css, re.S)

    for subset, body in blocks:
        if "latin-ext" not in subset:
            continue
        family_match = re.search(r"font-family:\s*['\"]?([^'\";]+)", body)
        weight_match = re.search(r"font-weight:\s*(\d+)", body)
        src_match = re.search(r"url\((https://[^)]+)\)", body)
        if not (family_match and weight_match and src_match):
            continue

        family = family_match.group(1).strip()
        weight = weight_match.group(1)
        filename = TARGETS.get((family, weight))
        if not filename:
            continue

        data = urllib.request.urlopen(src_match.group(1), timeout=60).read()
        path = OUT / filename
        path.write_bytes(data)
        print(f"Wrote {path.name} ({len(data):,} bytes)")

    found = sorted(p.name for p in OUT.glob("*.woff2"))
    missing = set(TARGETS.values()) - set(found)
    if missing:
        raise SystemExit(f"Missing fonts: {', '.join(sorted(missing))}")
    print(f"OK — {len(found)} font files")


if __name__ == "__main__":
    main()
