"""
Statičke fotografije iz static/img/ — karusel (početna) i galerija (usluge).
Dimenzije: izvorne WebP rezolucije (za aspect-ratio i CLS).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings


@dataclass(frozen=True)
class StaticImageSlide:
    """Jedna slika za karusel ili galeriju."""

    path: str
    width: int
    height: int
    alt: str
    caption: str = ""


def _img_dir() -> Path:
    return Path(settings.BASE_DIR) / "static" / "img"


def probe_dimensions(filename: str) -> tuple[int, int] | None:
    """Učitaj širinu/visinu iz fajla ako postoji (Pillow)."""
    full = _img_dir() / filename
    if not full.is_file():
        return None
    try:
        from PIL import Image

        with Image.open(full) as im:
            return im.size
    except Exception:
        return None


# Karusel — širi kadar / pregled radova na objektu (1–5)
WORK_CAROUSEL_SLIDES: list[StaticImageSlide] = [
    StaticImageSlide(
        "img/cementne-kosuljice1.webp",
        1600,
        1127,
        "Mašinska ugradnja cementne košuljice — pogled na izvedenu podlogu na objektu",
        "Ravna podloga spremna za završne obloge",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice2.webp",
        1200,
        1600,
        "Cementna košuljica na gradilištu — ugradnja na spratu",
        "Izvođenje na višim etažama",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice3.webp",
        1200,
        1514,
        "Detalj završene cementne košuljice uz zid",
        "Precizna obrada ivica",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice4.webp",
        1200,
        1519,
        "Površina cementne košuljice nakon mašinske ugradnje",
        "Ujednačena debljina sloja",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice5.webp",
        1200,
        1523,
        "Pripremljena podloga u stambenom prostoru",
        "Podloga pre postavljanja završnih obloga",
    ),
]

# Galerija — detalji i završna obrada (7–10; 6 se ne koristi)
SERVICES_GALLERY_IMAGES: list[StaticImageSlide] = [
    StaticImageSlide(
        "img/cementne-kosuljice7.webp",
        1200,
        1491,
        "Mašinsko doziranje i razastiranje mešavine za košuljicu",
        "Savremena oprema na gradilištu",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice8.webp",
        1200,
        1504,
        "Nivelisana cementna košuljica u toku izvođenja",
        "Kontrola ravnosti podloge",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice9.webp",
        1600,
        1118,
        "Široka površina izvedene cementne košuljice",
        "Veći objekti i otvoreni prostori",
    ),
    StaticImageSlide(
        "img/cementne-kosuljice10.webp",
        1200,
        1600,
        "Završna faza perdašenja cementne košuljice",
        "Priprema za sledeću fazu gradnje",
    ),
]
