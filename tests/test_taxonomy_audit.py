"""Issue #64: RED contracts for source-backed, comment-aware taxonomy audit."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from iip_tf.taxonomy_audit import (
    PINNED_TAXONOMY_BLOB,
    TaxonomyError,
    audit_native_taxonomies,
    audit_values,
    git_blob_sha,
    parse_taxonomies,
)

NS = "http://www.tei-c.org/ns/1.0"


def _source(
    *,
    repeated: bool = False,
    wrong_namespace: bool = False,
) -> bytes:
    xmlns = "urn:evil" if wrong_namespace else NS
    taxa = {
        "IIP-form": ("block", "Stone block"),
        "IIP-materials": ("clay", "Clay"),
        "IIP-genre": ("dedicatory", "Dedicatory"),
        "IIP-preservation": ("complete", "Complete"),
        "IIP-writing": ("painted", "Painted"),
        "IIP-religion": ("jewish", "Jewish"),
    }
    body = "".join(
        f'<taxonomy xml:id="{name}"><category xml:id="{category}">'
        f"<catDesc>{label}</catDesc></category></taxonomy>"
        for name, (category, label) in taxa.items()
    )
    if repeated:
        body += (
            '<taxonomy xml:id="duplicate"><category xml:id="jewish">'
            "<catDesc>Conflicting reuse</catDesc></category></taxonomy>"
        )
    return (
        f'<classDecl xmlns="{xmlns}" xml:lang="en" '
        'xmlns:xml="http://www.w3.org/XML/1998/namespace">'
        "<!-- <category xml:id=\"clay.terracotta\"><catDesc>NOT ACTIVE</catDesc></category> -->"
        f"{body}</classDecl>"
    ).encode()


def test_parses_only_active_taxonomies_and_excludes_xml_comments() -> None:
    registry = parse_taxonomies(_source())
    assert len(registry.taxonomies) == 6
    assert sum(len(t) for t in registry.taxonomies.values()) == 6
    assert registry.taxonomies["IIP-materials"]["clay"] == "Clay"
    assert "clay.terracotta" not in registry.taxonomies["IIP-materials"]
    assert registry.taxonomies["IIP-writing"]["painted"] == "Painted"


def test_rejects_forged_blob_wrong_namespace_and_reused_category_ids() -> None:
    source = _source()
    assert git_blob_sha(source) != PINNED_TAXONOMY_BLOB
    with pytest.raises(TaxonomyError, match="blob"):
        parse_taxonomies(source, expected_blob=PINNED_TAXONOMY_BLOB)
    with pytest.raises(TaxonomyError, match="namespace"):
        parse_taxonomies(_source(wrong_namespace=True))
    with pytest.raises(TaxonomyError, match="duplicate"):
        parse_taxonomies(_source(repeated=True))


def test_literal_taxonomy_mapping_preserves_raw_values_and_ref_syntax() -> None:
    registry = parse_taxonomies(_source())
    report = audit_values(
        registry,
        {
            "religion": Counter({"jewish": 2, "#jewish": 5, "Jewish": 1}),
            "material": Counter(
                {"clay": 3, "clay.terracotta": 1, "jewish": 1, "clay stone": 1}
            ),
            "genre": Counter({"#dedicatory": 4}),
            "object_type": Counter({"#block": 1}),
            "condition": Counter({"complete": 1}),
        },
    )
    rows = {
        row["raw"]: row
        for row in report["fields"]["religion"]["values"]
    }
    assert rows["#jewish"]["category_id"] == "jewish"
    assert rows["#jewish"]["count"] == 5
    assert rows["jewish"]["category_id"] == "jewish"
    assert rows["Jewish"]["status"] == "unresolved"
    material = {
        row["raw"]: row for row in report["fields"]["material"]["values"]
    }
    assert material["clay.terracotta"]["status"] == "unresolved"
    assert material["jewish"]["status"] == "wrong_taxonomy"
    assert material["clay stone"]["status"] == "multiple_tokens"
    assert material["clay"]["category_id"] == "clay"
    assert report["fields"]["genre"]["taxonomy_id"] == "IIP-genre"
    assert report["taxonomy_count"] == 6
    assert report["active_category_count"] == 6
    assert report["fields"]["religion"]["observed_count"] == 8
    assert report["fields"]["religion"]["unresolved_count"] == 1
    assert json.dumps(report, sort_keys=True, ensure_ascii=False)


def test_real_native_feature_api_is_queried_without_sidecar() -> None:
    registry = parse_taxonomies(_source())

    class Feature:
        def __init__(self, values: dict[int, str]) -> None:
            self.values = values

        def items(self) -> Any:
            return self.values.items()

    features = {
        "religion": Feature({1: "#jewish", 2: "jewish"}),
        "material": Feature({1: "clay"}),
        "genre": Feature({1: "#dedicatory"}),
        "object_type": Feature({1: "block"}),
        "condition": Feature({1: "complete"}),
    }
    api = SimpleNamespace(Fs=lambda name: features[name])
    report = audit_native_taxonomies(api, registry)
    assert report["fields"]["religion"]["observed_count"] == 2
    assert report["fields"]["material"]["resolved_count"] == 1
    assert set(report["fields"]) == set(features)


def test_guide_discusses_comment_inflation_and_no_silent_normalization() -> None:
    root = Path(__file__).resolve().parents[1]
    guide = (root / "docs/guides/pinned-taxonomy-audit.md").read_text(
        encoding="utf-8"
    )
    assert "142" in guide
    assert "23" in guide
    assert "taxonomy-audit.json" in guide
    assert "does not normalize" in guide.lower()


def test_multivalue_taxonomy_tokens_preserve_order_duplicates_and_unknowns() -> None:
    # The source refs are TEI IDREFS lists, not scalar categories.
    source = _source().replace(
        b'<category xml:id="jewish">',
        (
            b'<category xml:id="other_religion">'
            b'<catDesc>Other</catDesc></category><category xml:id="jewish">'
        ),
    )
    registry = parse_taxonomies(source)
    report = audit_values(
        registry,
        {
            "genre": Counter({"#dedicatory #Quotation": 1}),
            "material": Counter({"clay": 1}),
            "religion": Counter(
                {"#jewish #other_religion": 2, "jewish jewish": 1}
            ),
            "object_type": Counter(
                {"block block": 1, "#jewish block": 1, "alien nonexistent": 1}
            ),
            "condition": Counter({"complete": 1}),
        },
    )
    religion = report["fields"]["religion"]
    row = next(v for v in religion["values"] if v["raw"] == "#jewish #other_religion")
    assert row["status"] == "multiple_tokens"  # preserve previous report shape
    assert row["tokens"] == [
        {"index": 0, "raw": "#jewish", "status": "resolved", "category_id": "jewish"},
        {
            "index": 1, "raw": "#other_religion",
            "status": "resolved", "category_id": "other_religion",
        },
    ]
    duplicated = next(v for v in religion["values"] if v["raw"] == "jewish jewish")
    assert duplicated["tokens"][0]["category_id"] == "jewish"
    assert duplicated["tokens"][1]["category_id"] == "jewish"
    assert [v["index"] for v in duplicated["tokens"]] == [0, 1]
    assert religion["multivalue_resolution"] == {
        "fully_resolved": 3, "partially_resolved": 0, "no_resolved": 0,
    }
    genre = report["fields"]["genre"]
    assert genre["multivalue_resolution"]["partially_resolved"] == 1
    assert genre["values"][0]["tokens"][1] == {
        "index": 1, "raw": "#Quotation", "status": "unresolved",
    }
    object_type = report["fields"]["object_type"]
    assert object_type["multivalue_resolution"] == {
        "fully_resolved": 1, "partially_resolved": 1, "no_resolved": 1,
    }
    mixed = next(v for v in object_type["values"] if v["raw"] == "#jewish block")
    assert [v["status"] for v in mixed["tokens"]] == [
        "wrong_taxonomy", "resolved",
    ]
    assert report["multivalue_resolution"] == {
        "fully_resolved": 4, "partially_resolved": 2, "no_resolved": 1,
    }
    assert report["fields"]["material"]["multivalue_resolution"] == {
        "fully_resolved": 0, "partially_resolved": 0, "no_resolved": 0,
    }


def test_pinned_multivalue_snapshot_is_source_authenticated() -> None:
    import iip_tf.taxonomy_audit as taxonomy_audit
    assert vars(taxonomy_audit)["EXPECTED_PINNED_MULTIVALUE"] == {
        "fully_resolved": 402, "partially_resolved": 126, "no_resolved": 2,
    }
