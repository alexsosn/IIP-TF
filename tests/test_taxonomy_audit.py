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
