from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schema" / "iip-tf-0.1.json"
ADR = ROOT / "docs" / "architecture" / "ADR-0001-native-tf-schema.md"
REFERENCE = ROOT / "docs" / "reference" / "schema-0.1.md"


def _schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_schema_freezes_single_sign_warp_and_native_text_layers() -> None:
    schema = _schema()

    assert schema["schema_version"] == "0.1"
    assert schema["warp"]["slot_type"] == "sign"
    assert schema["warp"]["text_layers"] == [
        "transcription",
        "diplomatic",
        "translation",
        "commentary",
    ]
    assert schema["warp"]["segmented_transcription_role"] == "annotation_only"


def test_primary_text_policy_is_non_guessing() -> None:
    schema = _schema()
    primary = schema["primary_text"]

    assert primary["selection_order"] == ["transcription", "diplomatic", "empty_anchor"]
    assert primary["segmented_transcription_is_primary_fallback"] is False
    assert primary["empty_anchor"]["fabricates_visible_text"] is False
    assert primary["word_fallback"] == "none"


def test_sections_and_formats_are_standard_tf_oriented() -> None:
    schema = _schema()

    assert schema["sections"] == {
        "types": ["inscription", "textpart", "line"],
        "features": ["inscription_id", "section_part", "line_n"],
    }
    formats = schema["text_formats"]
    assert formats["text-orig-full"]["purpose"] == "primary"
    assert formats["text-layer-full"]["purpose"] == "current_layer"
    assert formats["text-diplomatic-full"]["purpose"] == "diplomatic"
    assert formats["text-translation-full"]["purpose"] == "translation"


def test_required_node_types_and_native_metadata_are_frozen() -> None:
    schema = _schema()
    node_types = set(schema["node_types"])

    assert {
        "inscription",
        "edition",
        "textpart",
        "line",
        "word",
        "markup",
        "entity",
        "segmentation",
        "bibl",
        "hand",
        "decoration",
        "image",
        "revision",
    } <= node_types

    metadata = schema["metadata_policy"]
    assert metadata["opaque_sidecars"] is False
    assert metadata["raw_xml_or_json_blobs"] is False
    assert metadata["image_binaries_in_corpus"] is False


def test_slot_markup_and_edge_features_preserve_source_semantics() -> None:
    schema = _schema()
    slot_features = set(schema["features"]["slot"])
    node_features = set(schema["features"]["node"])
    edge_features = set(schema["features"]["edge"])

    assert {
        "glyph",
        "after",
        "layer",
        "lang",
        "lang_source",
        "synthetic_kind",
        "primary_glyph",
        "primary_after",
    } <= slot_features
    assert {
        "source_id",
        "source_key",
        "kind",
        "reason",
        "cert",
        "unit",
        "quantity",
        "extent",
        "ref",
        "value",
        "rend",
        "primary_layer",
    } <= node_features
    assert {
        "parent",
        "in_inscription",
        "corresponds_to",
        "cites",
        "segmentation_of",
        "token_from",
    } <= edge_features


def test_zero_width_and_metadata_anchoring_rules_are_explicit() -> None:
    schema = _schema()
    anchors = schema["anchoring"]

    assert anchors["zero_width_source_positions"]["slot_policy"] == "one_synthetic_sign_per_event"
    assert anchors["zero_width_source_positions"]["quantity_does_not_multiply_slots"] is True
    assert anchors["metadata"]["uses_existing_primary_anchor_when_available"] is True
    assert anchors["metadata"]["creates_anchor_only_if_no_primary_slot_exists"] is True


def test_editorial_markup_is_structured_not_opaque() -> None:
    schema = _schema()
    kinds = set(schema["markup"]["kinds"])

    assert {
        "supplied",
        "unclear",
        "gap",
        "choice",
        "sic",
        "corr",
        "orig",
        "reg",
        "expan",
        "abbr",
        "ex",
        "am",
        "del",
        "surplus",
        "space",
        "glyph",
        "num",
        "foreign",
        "hi",
        "hand_shift",
        "column_break",
        "milestone",
        "apparatus",
        "lemma",
        "reading",
    } <= kinds
    assert schema["markup"]["raw_attributes_blob"] is False
    assert schema["markup"]["preserve_direct_parent_edge"] is True


def test_provenance_and_rights_boundary_are_frozen() -> None:
    schema = _schema()
    provenance = schema["provenance"]

    assert provenance["source_repository"] == "Brown-University-Library/iip-texts"
    assert provenance["source_revision"] == "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"
    assert provenance["doi"] == "10.26300/pz1d-st89"
    assert provenance["generated_data_license"] == "CC BY-NC 4.0"
    assert provenance["software_license"] == "MIT"


def test_human_documents_exist_and_state_no_raw_blob_escape_hatch() -> None:
    adr = ADR.read_text(encoding="utf-8")
    ref = REFERENCE.read_text(encoding="utf-8")

    assert "single `sign` warp" in adr
    assert "transcription_segmented" in adr
    assert "No raw XML or JSON blob" in adr
    assert "## Node types" in ref
    assert "## Text formats" in ref


def test_record_identity_is_file_scoped_not_upstream_id_scoped() -> None:
    schema = _schema()
    identity = schema["identity"]

    assert identity["canonical_record_key"] == "source_file_stem"
    assert identity["section_feature"] == "inscription_id"
    assert identity["iip_id_is_globally_unique"] is False
    assert identity["xml_id_is_globally_unique"] is False
    assert identity["source_element_ids_are_scoped_by_file"] is True
    assert identity["bare_local_corresp_resolution_scope"] == "source_file"


def test_textual_blocks_preserve_paragraph_and_ab_boundaries() -> None:
    schema = _schema()
    node_types = set(schema["node_types"])

    assert "paragraph" in node_types
    paragraph = schema["node_type_contract"]["paragraph"]
    assert paragraph["source_elements"] == ["p", "ab"]
    assert {"kind", "lang", "cert", "source_id", "source_key"} <= set(
        paragraph["features"]
    )


def test_tf_feature_value_types_are_single_and_serializable() -> None:
    schema = _schema()
    types = schema["tf_value_types"]

    assert types["slot_default"] == "str"
    assert types["node_default"] == "str"
    assert types["edge_default"] == "edge_without_values"
    assert {"line_n", "quantity_int", "date_not_before_int", "date_not_after_int"} <= set(
        types["node_int"]
    )
    assert schema["feature_contract"]["quantity"]["value_type"] == "str"
    assert schema["feature_contract"]["quantity_int"]["value_type"] == "int"
    assert schema["feature_contract"]["date_not_before"]["value_type"] == "str"
    assert schema["feature_contract"]["date_not_before_int"]["value_type"] == "int"


def test_repeatable_bibliography_scopes_are_native_nodes() -> None:
    schema = _schema()

    assert "bibl_scope" in set(schema["node_types"])
    assert "bibl_scope" in set(schema["metadata_policy"]["repeatable_nodes"])
    assert schema["metadata_nodes"]["bibl_scope"]["parent_type"] == "bibl"
    assert set(schema["metadata_nodes"]["bibl_scope"]["features"]) >= {
        "scope",
        "scope_unit",
        "scope_n",
    }


def test_physical_dimensions_are_repeatable_native_nodes() -> None:
    schema = _schema()

    assert "dimension" in set(schema["node_types"])
    assert "dimension" in set(schema["metadata_policy"]["repeatable_nodes"])
    dimension = schema["metadata_nodes"]["dimension"]
    assert dimension["raw_values_are_strings"] is True
    assert {
        "dimension_type",
        "dimension_extent",
        "dimension_unit",
        "height",
        "height_min",
        "height_max",
        "width",
        "width_min",
        "width_max",
        "depth",
        "depth_min",
        "depth_max",
        "quantity",
        "at_least",
        "at_most",
    } <= set(dimension["features"])


def test_facsimile_surface_grouping_is_preserved() -> None:
    schema = _schema()

    assert "facsimile_surface" in set(schema["node_types"])
    assert "facsimile_surface" in set(schema["metadata_policy"]["repeatable_nodes"])
    surface = schema["metadata_nodes"]["facsimile_surface"]
    assert {"description", "note"} <= set(surface["features"])
    assert schema["metadata_nodes"]["image"]["parent_policy"] == (
        "facsimile_surface_when_present_else_inscription"
    )
