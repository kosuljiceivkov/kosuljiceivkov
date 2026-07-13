"""Zajednički page fixture-i za testove."""

from __future__ import annotations

from apps.page.schema import empty_page
from apps.page.structure import (
    create_divider_block,
    create_heading_block,
    create_row,
    create_section,
    create_text_block,
)


def sample_page() -> dict:
    page = empty_page()

    hero = create_section(section_id="sec_demo_hero")
    hero_col = hero["rows"][0]["columns"][0]
    hero_col["blocks"] = [
        create_heading_block(level=1, text="Naslov stranice"),
        create_text_block(text="Kratak uvodni tekst koji objašnjava sadržaj stranice."),
    ]

    cta_section = create_section(section_id="sec_demo_cta")
    cta_section["settings"]["background"] = "light"
    cta_row = create_row(preset="one")
    cta_col = cta_row["columns"][0]
    cta_col["blocks"] = [
        create_heading_block(level=2, text="Spremni za sledeći korak?"),
        create_text_block(text="Kontaktirajte nas i saznajte više o našim uslugama."),
    ]
    cta_section["rows"] = [cta_row]

    page["sections"] = [hero, cta_section]
    return page
