from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schema" / "iip-tf-0.1.json"
REFERENCE = ROOT / "docs" / "reference" / "schema-0.1.md"
ADR = ROOT / "docs" / "architecture" / "ADR-0001-native-tf-schema.md"


def _schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_support_notes_are_repeatable_native_nodes_not_scalar_metadata() -> None:
    schema = _schema()

    assert "support_note" in schema["node_types"]
    assert "support_note" in schema["metadata_policy"]["repeatable_nodes"]
    assert "support_note" not in schema["metadata_policy"]["scalar_on_inscription"]
    assert schema["metadata_nodes"]["support_note"] == {
        "parent_type": "inscription",
        "features": ["source_key", "note"],
    }


def test_facsimile_surface_preserves_nested_surface_hierarchy() -> None:
    schema = _schema()

    surface = schema["metadata_nodes"]["facsimile_surface"]
    assert surface["parent_types"] == ["inscription", "facsimile_surface"]
    assert "parent_type" not in surface


def test_human_schema_docs_explain_both_shape_exceptions() -> None:
    reference = REFERENCE.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")

    assert "one `support_note` node per non-empty direct `support/p`" in reference
    assert "nested `facsimile_surface`" in reference
    assert "repeatable support paragraphs" in adr
    assert "nested facsimile surfaces" in adr
