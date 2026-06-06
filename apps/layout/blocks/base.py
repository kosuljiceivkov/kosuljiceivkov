"""Osnovni tipovi za block plugin sistem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class BlockStorage(str, Enum):
    """Način skladištenja podataka bloka."""

    LEGACY = "legacy"
    CONFIG = "config"
    RELATED = "related"


@dataclass(frozen=True)
class AdminFieldset:
    """Jedan fieldset u Django adminu za tip bloka."""

    title: str | None
    fields: tuple[str, ...]
    css_suffix: str


@dataclass(frozen=True)
class BlockTypePlugin:
    """
    Definicija jednog tipa bloka u registru.

    Novi tipovi koriste CONFIG ili RELATED; postojeći tipovi koriste LEGACY kolone.
    """

    type_id: str
    label: str
    template: str
    storage: BlockStorage = BlockStorage.LEGACY
    admin_fieldsets: tuple[AdminFieldset, ...] = ()
    needs_gallery: bool = False
    needs_carousel: bool = False
    enabled: bool = True
    description: str = ""
    validate: Callable[[Any], None] | None = None
    get_context: Callable[[Any], dict[str, Any]] | None = None
    future: bool = False

    def admin_css_class(self) -> str:
        return f"builder-block-fields--{self.type_id}"

    def build_admin_fieldsets(self) -> tuple[tuple, ...]:
        fieldsets = []
        for admin_fieldset in self.admin_fieldsets:
            fieldsets.append(
                (
                    admin_fieldset.title,
                    {
                        "fields": admin_fieldset.fields,
                        "classes": (
                            "builder-block-fields",
                            admin_fieldset.css_suffix,
                        ),
                    },
                )
            )
        if self.storage is BlockStorage.CONFIG:
            fieldsets.append(
                (
                    "Konfiguracija",
                    {
                        "fields": ("config",),
                        "classes": (
                            "builder-block-fields",
                            self.admin_css_class(),
                        ),
                        "description": self.description,
                    },
                )
            )
        return tuple(fieldsets)

    def get_render_context(self, block) -> dict[str, Any]:
        if self.get_context is not None:
            return self.get_context(block)
        return {}

    def run_validation(self, block) -> None:
        if self.validate is not None:
            self.validate(block)
