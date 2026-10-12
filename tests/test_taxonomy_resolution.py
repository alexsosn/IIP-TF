"""#64 RED: only authentic source-taxonomy category IDs enter native metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.taxonomy_audit import TaxonomyRegistry
from iip_tf.taxonomy_resolution import resolve_taxonomy_features
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _vocabulary() -> TaxonomyRegistry:
    return TaxonomyRegistry({
        "IIP-form": {"block": "Block"},
        "IIP-materials": {"clay": "Clay", "stone": "Stone"},
        "IIP-genre": {"dedicatory": "Dedicatory"},
        "IIP-preservation": {"complete": "Complete"},
        "IIP-writing": {"painted": "Painted"},
        "IIP-religion": {"jewish": "Jewish", "pagan": "Pagan"},
    })


def _xml(tmp_path: Path, *, religion: str = "#jewish") -> Path:
    path = tmp_path / "demo0001.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><titleStmt><title>Taxon</title></titleStmt>'
        '<sourceDesc><msDesc><msContents><textLang mainLang="heb"/>'
        f'<msItem class="#dedicatory" ana="{religion}"><p/></msItem>'
        '</msContents></msDesc></sourceDesc></fileDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription">'
        '<p>אב</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    return path


def test_hashless_and_hashprefixed_idrefs_canonicalize_without_fuzzy(
    tmp_path: Path,
) -> None:
    for raw in ("jewish", "#jewish"):
        ir = parse_epidoc_file(_xml(tmp_path, religion=raw),
                               source_revision="fixture")
        before = ir.node_feature(NodeType.INSCRIPTION, "religion")
        result, audit = resolve_taxonomy_features(ir, _vocabulary())
        assert before == raw
        assert result.node_feature(NodeType.INSCRIPTION, "religion") == "jewish"
        assert result.node_feature(NodeType.INSCRIPTION, "religion_original") == raw
        assert result.node_feature(NodeType.INSCRIPTION, "genre") == "dedicatory"
        assert result.node_feature(NodeType.INSCRIPTION, "genre_original") == "#dedicatory"
        assert audit["normalized_fields"] == 2
        assert audit["unresolved_fields"] == {}
        assert result.signs == ir.signs and result.edges == ir.edges


def test_multivalued_resolves_only_when_all_tokens_have_same_taxonomy(
    tmp_path: Path,
) -> None:
    ir = parse_epidoc_file(_xml(tmp_path, religion="#jewish pagan #jewish"),
                           source_revision="fixture")
    result, audit = resolve_taxonomy_features(ir, _vocabulary())
    assert result.node_feature(NodeType.INSCRIPTION, "religion") == (
        "jewish pagan jewish"
    )
    assert result.node_feature(NodeType.INSCRIPTION, "religion_original") == (
        "#jewish pagan #jewish"
    )
    assert audit["normalized_fields"] == 2

    for raw in ("#jewish #unknown", "#jewish #stone", "Jewish", "clay"):
        original = parse_epidoc_file(_xml(tmp_path, religion=raw),
                                     source_revision="fixture")
        linked, report = resolve_taxonomy_features(original, _vocabulary())
        assert linked.node_feature(NodeType.INSCRIPTION, "religion") is None
        assert linked.node_feature(NodeType.INSCRIPTION, "religion_original") == raw
        assert report["unresolved_fields"] == {"religion": 1}
        assert original.node_feature(NodeType.INSCRIPTION, "religion") == raw


def test_missing_taxonomy_source_feature_is_not_forged(tmp_path: Path) -> None:
    ir = parse_epidoc_file(_xml(tmp_path), source_revision="fixture")
    normalized, audit = resolve_taxonomy_features(ir, _vocabulary())
    for feature in ("material", "condition", "object_type"):
        assert normalized.node_feature(NodeType.INSCRIPTION, feature) is None
        assert normalized.node_feature(NodeType.INSCRIPTION, feature + "_original") is None
    assert audit["normalized_fields"] == 2


def test_native_fabric_reload_retains_original_and_canonical_queries(
    tmp_path: Path,
) -> None:
    ir = parse_epidoc_file(_xml(tmp_path, religion="#jewish"), source_revision="fixture")
    normalized, _ = resolve_taxonomy_features(ir, _vocabulary())
    out = tmp_path / "native"
    write_tf_corpus((normalized,), out, converter_commit="test")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    root = api.T.nodeFromSection(("demo0001",))
    assert root is not None
    assert api.F.religion.v(root) == "jewish"
    assert api.F.religion_original.v(root) == "#jewish"
    assert api.F.genre.v(root) == "dedicatory"
    assert api.F.genre_original.v(root) == "#dedicatory"
    assert api.T.text(root) == "אב"
    assert api.F.otype.s("person") == ()


def test_feature_resolution_rejects_double_normalization(tmp_path: Path) -> None:
    ir = parse_epidoc_file(_xml(tmp_path), source_revision="fixture")
    normalized, _ = resolve_taxonomy_features(ir, _vocabulary())
    try:
        resolve_taxonomy_features(normalized, _vocabulary())
    except ValueError as error:
        assert "already" in str(error)
    else:
        raise AssertionError("re-augmenting taxonomy must fail closed")
