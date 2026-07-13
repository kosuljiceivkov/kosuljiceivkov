"""Element catalog metadata for structure-first builder."""

from __future__ import annotations

from apps.page.structure import ROW_PRESETS

BUILDER_ELEMENTS = (
    {
        "id": "heading",
        "label": "Naslov",
        "description": "H1–H4 (nivo je semantički; veličina i format ručno)",
    },
    {"id": "text", "label": "Tekst", "description": "Paragraf"},
    {"id": "image", "label": "Slika", "description": "Slika sa alt tekstom"},
    {"id": "video", "label": "Video", "description": "YouTube video"},
    {"id": "faq", "label": "FAQ", "description": "Pitanja i odgovori"},
    {"id": "button", "label": "Dugme", "description": "CTA link dugme"},
    {"id": "divider", "label": "Linija", "description": "Horizontalna linija"},
)

ROW_PRESET_LABELS = {
    "one": "1 kolona",
    "two_equal": "2 jednake kolone",
    "two_66_33": "2 kolone (66% / 33%)",
    "two_33_66": "2 kolone (33% / 66%)",
    "three_equal": "3 jednake kolone",
}


def build_builder_catalog() -> dict:
    return {
        "elements": list(BUILDER_ELEMENTS),
        "row_presets": [
            {"id": preset_id, "label": ROW_PRESET_LABELS.get(preset_id, preset_id)}
            for preset_id in ROW_PRESETS
        ],
        "section_settings": [
            {"id": "padding_top", "label": "Gornji padding", "type": "enum", "options": ["none", "sm", "md", "lg"]},
            {"id": "padding_bottom", "label": "Donji padding", "type": "enum", "options": ["none", "sm", "md", "lg"]},
            {"id": "margin_top", "label": "Gornja margina", "type": "enum", "options": ["none", "sm", "md", "lg"]},
            {"id": "margin_bottom", "label": "Donja margina", "type": "enum", "options": ["none", "sm", "md", "lg"]},
            {"id": "background", "label": "Pozadina", "type": "enum", "options": ["default", "light", "dark", "accent"]},
            {"id": "container_width", "label": "Širina", "type": "enum", "options": ["contained", "full"]},
        ],
        "row_settings": [
            {"id": "column_gap", "label": "Razmak kolona", "type": "enum", "options": ["none", "sm", "md", "lg"]},
            {"id": "vertical_align", "label": "Vertikalno", "type": "enum", "options": ["top", "center", "bottom"]},
        ],
        "column_settings": [
            {"id": "padding", "label": "Padding", "type": "enum", "options": ["none", "sm", "md", "lg"]},
            {"id": "horizontal_align", "label": "Poravnanje", "type": "enum", "options": ["left", "center", "right"]},
        ],
        "block_settings": [
            {"id": "align", "label": "Poravnanje teksta", "type": "enum", "options": ["left", "center", "right"]},
        ],
    }
