"""#100 RED-first end-user taxonomy lookup contracts over original source IDREFs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iip_tf.cli import main as cli_main
from iip_tf.taxonomy_audit import (
    PINNED_SOURCE_REVISION,
    TaxonomyError,
    parse_taxonomies,
)
from iip_tf.taxonomy_lookup import lookup_taxonomy_labels


def _source() -> bytes:
    taxonomies = {
        "IIP-form": (("block", "Block"),),
        "IIP-materials": (
            ("stone", "Stone"),
            ("stone.other", "Other Stone"),
            ("clay", "Clay"),
        ),
        "IIP-genre": (("funerary", "Funerary"), ("funerary.epitaph", "Epitaph")),
        "IIP-preservation": (("complete", "Complete"), ("fragment.single", "Single Fragment")),
        "IIP-writing": (("painted", "Painted"),),
        "IIP-religion": (("jewish", "Jewish"),),
    }
    xml = '<classDecl xmlns="http://www.tei-c.org/ns/1.0">'
    for taxonomy, categories in taxonomies.items():
        xml += f'<taxonomy xml:id="{taxonomy}">'
        for category, label in categories:
            xml += f'<category xml:id="{category}"><catDesc>{label}</catDesc></category>'
        if taxonomy == "IIP-materials":
            xml += ('<!-- <category xml:id="clay.terracotta">'
                    '<catDesc>Terracotta</catDesc></category> -->')
        xml += '</taxonomy>'
    return (xml + '</classDecl>').encode("utf-8")


def test_resolves_ordered_multivalue_ref_labels_without_deduplication() -> None:
    registry = parse_taxonomies(_source())
    result = lookup_taxonomy_labels(
        registry, "material", " #stone.other clay #stone.other "
    )
    assert result["feature"] == "material"
    assert result["taxonomy_id"] == "IIP-materials"
    assert result["raw"] == " #stone.other clay #stone.other "
    assert result["resolution"] == "fully_resolved"
    assert result["tokens"] == [
        {
            "index": 0, "raw": "#stone.other", "status": "resolved",
            "category_id": "stone.other", "label": "Other Stone",
            "dotted_prefix_candidate": "stone",
        },
        {
            "index": 1, "raw": "clay", "status": "resolved",
            "category_id": "clay", "label": "Clay",
        },
        {
            "index": 2, "raw": "#stone.other", "status": "resolved",
            "category_id": "stone.other", "label": "Other Stone",
            "dotted_prefix_candidate": "stone",
        },
    ]
    assert "parent" not in str(result)
    assert "is_a" not in str(result)


def test_dotted_id_without_active_prefix_does_not_forge_hierarchy() -> None:
    # Authentic Brown IIP-preservation has fragment.single but no fragment.
    registry = parse_taxonomies(_source())
    result = lookup_taxonomy_labels(registry, "condition", "#fragment.single")
    assert result["resolution"] == "fully_resolved"
    assert result["tokens"] == [{
        "index": 0,
        "raw": "#fragment.single",
        "status": "resolved",
        "category_id": "fragment.single",
        "label": "Single Fragment",
    }]


def test_unresolved_tokens_never_receive_a_label_or_partial_canonical() -> None:
    registry = parse_taxonomies(_source())
    result = lookup_taxonomy_labels(
        registry, "material", "#stone.other #jewish #Stone #clay.terracotta"
    )
    assert result["resolution"] == "partially_resolved"
    assert [v["status"] for v in result["tokens"]] == [
        "resolved", "wrong_taxonomy", "case_mismatch", "unknown",
    ]
    for token in result["tokens"][1:]:
        assert "label" not in token and "category_id" not in token
    assert "canonical" not in result
    assert result["tokens"][3]["raw"] == "#clay.terracotta"
    # A commented source category-like string is not an active classification.
    assert lookup_taxonomy_labels(
        registry, "material", "clay.terracotta"
    )["resolution"] == "unresolved"


def test_empty_and_unknown_feature_fail_closed() -> None:
    registry = parse_taxonomies(_source())
    assert lookup_taxonomy_labels(registry, "religion", " \t ")["tokens"] == []
    assert lookup_taxonomy_labels(registry, "religion", " \t ")["resolution"] == (
        "unresolved"
    )
    with pytest.raises(TaxonomyError, match="unsupported classification feature"):
        lookup_taxonomy_labels(registry, "faith", "jewish")
    with pytest.raises(TaxonomyError, match="source text"):
        lookup_taxonomy_labels(registry, "religion", 7)  # type: ignore[arg-type]


def test_cli_lookup_is_stable_and_labels_unpinned_source_honestly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "include_taxonomies.xml"
    source.write_bytes(_source())
    argv = ["taxonomy-lookup", str(source), "material", "#stone.other #jewish"]
    assert cli_main(argv) == 0
    first = capsys.readouterr().out
    assert cli_main(argv) == 0
    second = capsys.readouterr().out
    assert first == second
    result = json.loads(first)
    assert result["source_revision"] is None
    assert len(result["taxonomy_git_blob"]) == 40
    assert result["resolution"] == "partially_resolved"
    assert result["tokens"][0]["label"] == "Other Stone"
    with pytest.raises(TaxonomyError, match="blob"):
        cli_main([*argv, "--source-revision", PINNED_SOURCE_REVISION])


def test_cli_missing_taxonomy_is_not_accepted(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="taxonomy source"):
        cli_main(["taxonomy-lookup", str(tmp_path / "missing.xml"), "material", "clay"])
