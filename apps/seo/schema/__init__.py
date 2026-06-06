"""Schema.org JSON-LD engine — generisanje, validacija i preview."""

from apps.seo.schema.engine import (
    build_schema_graph,
    collect_json_ld_schemas,
    serialize_schema_graph,
)
from apps.seo.schema.validation import SchemaValidationResult, validate_schema_graph

__all__ = (
    "build_schema_graph",
    "collect_json_ld_schemas",
    "serialize_schema_graph",
    "SchemaValidationResult",
    "validate_schema_graph",
)
