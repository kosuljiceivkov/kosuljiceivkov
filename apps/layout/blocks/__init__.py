"""Block plugin paket — skalabilna arhitektura tipova blokova."""

from apps.layout.blocks.registry import (
    build_block_admin_fieldsets,
    get_block_plugin,
    get_block_render_context,
    get_block_template_name,
    get_enabled_plugins,
    register_block_plugin,
    validate_block,
)

__all__ = [
    "build_block_admin_fieldsets",
    "get_block_plugin",
    "get_block_render_context",
    "get_block_template_name",
    "get_enabled_plugins",
    "register_block_plugin",
    "validate_block",
]
