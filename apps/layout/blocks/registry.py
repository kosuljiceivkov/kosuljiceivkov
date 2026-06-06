"""Centralni registar tipova blokova."""

from __future__ import annotations

from typing import Any

from apps.layout.blocks.base import BlockTypePlugin
from apps.layout.blocks.legacy_plugins import LEGACY_PLUGINS

_PLUGINS: dict[str, BlockTypePlugin] = {}


def _register_plugins(plugins: tuple[BlockTypePlugin, ...]) -> None:
    for plugin in plugins:
        _PLUGINS[plugin.type_id] = plugin


_register_plugins(LEGACY_PLUGINS)


def register_block_plugin(plugin: BlockTypePlugin) -> None:
    """Registruje ili zamenjuje plugin (za proširenja i testove)."""
    _PLUGINS[plugin.type_id] = plugin


def get_block_plugin(block_type: str) -> BlockTypePlugin | None:
    return _PLUGINS.get(block_type)


def get_enabled_plugins() -> list[BlockTypePlugin]:
    return [plugin for plugin in _PLUGINS.values() if plugin.enabled and not plugin.future]


def get_block_template_name(block_type: str) -> str:
    plugin = get_block_plugin(block_type)
    if plugin is None:
        return "builder/blocks/unknown.html"
    return plugin.template


def get_block_render_context(block) -> dict[str, Any]:
    plugin = get_block_plugin(block.block_type)
    if plugin is None:
        return {}
    return plugin.get_render_context(block)


def validate_block(block) -> None:
    plugin = get_block_plugin(block.block_type)
    if plugin is None:
        return
    plugin.run_validation(block)


def build_block_admin_fieldsets() -> tuple[tuple, ...]:
    """Sastavlja Django admin fieldsets za BlockInline iz registra."""
    fieldsets: list[tuple] = [
        (
            None,
            {
                "fields": ("order", "block_type"),
                "classes": ("builder-block-root-marker",),
            },
        ),
    ]

    for plugin in get_enabled_plugins():
        if plugin.storage.value == "legacy":
            fieldsets.extend(plugin.build_admin_fieldsets())

    for plugin in get_enabled_plugins():
        if plugin.storage.value == "config":
            fieldsets.extend(plugin.build_admin_fieldsets())

    return tuple(fieldsets)
