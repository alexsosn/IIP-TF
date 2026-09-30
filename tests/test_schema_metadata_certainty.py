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


def test_metadata_certainty_paths_have_distinct_raw_string_features() -> None:
    schema = _schema()
    required = {
        "genre_cert",
        "date_precision",
        "region_cert",
        "settlement_cert",
    }

    assert required <= set(schema["metadata_policy"]["scalar_on_inscription"])
    assert required <= set(schema["features"]["node"])
    for feature in required:
        assert schema["feature_contract"][feature]["domain"] == "inscription"
        assert schema["feature_contract"][feature]["value_type"] == "str"


def test_metadata_attribute_mapping_keeps_certainty_context() -> None:
    schema = _schema()
    mapping = schema["metadata_source_attribute_mapping"]

    assert mapping["msItem@cert"] == "genre_cert"
    assert mapping["origin/date@precision"] == "date_precision"
    assert mapping["origin/region@cert"] == "region_cert"
    assert mapping["origin/settlement@cert"] == "settlement_cert"


def test_human_schema_docs_name_path_specific_metadata_certainty() -> None:
    adr = ADR.read_text(encoding="utf-8")
    reference = REFERENCE.read_text(encoding="utf-8")

    for feature in ("genre_cert", "date_precision", "region_cert", "settlement_cert"):
        assert feature in adr
        assert feature in reference
