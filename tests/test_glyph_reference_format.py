"""Issue #58: opt-in glyph-reference text without inventing source letters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import TFWriterError, write_tf_corpus


def _source(tmp_path: Path, record_id: str, text: str, layer: str = "transcription") -> Path:
    source = tmp_path / f"{record_id}.xml"
    source.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Glyph fixture</title>"
        "<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>"
        "</titleStmt><publicationStmt><idno>source</idno></publicationStmt>"
        "</fileDesc></teiHeader>"
        f'<text><body><div type="edition" subtype="{layer}"><p>'
        f"{text}</p></div></body></text></TEI>",
        encoding="utf-8",
    )
    return source


@pytest.fixture
def glyph_api(tmp_path: Path) -> Any:
    fixtures = [
        ("masa0286", '<g ref="phoen-gaml"/><g ref="phoen-delt"/>', "transcription"),
        ("mixed", 'A<g ref="phoen-gaml"/>B<g ref="cross">+</g>C', "transcription"),
        ("branch", '<choice><orig>x</orig><reg>y</reg></choice><g ref="bird"/>', "transcription"),
        ("dipl", '<g ref="phoen-wau"/>Z', "diplomatic"),
        ("danger", '<g ref="&lt;script&gt;"/>Q', "transcription"),
    ]
    irs = tuple(
        parse_epidoc_file(
            _source(tmp_path, record_id, text, layer), source_revision="fixture-revision"
        )
        for record_id, text, layer in fixtures
    )
    tf_dir = tmp_path / "tf"
    write_tf_corpus(irs, tf_dir, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(tf_dir), silent=True).loadAll(silent=True)
    assert api
    return api


def test_all_glyph_reference_inscription_remains_empty_in_original(glyph_api: Any) -> None:
    api = glyph_api
    n = api.T.nodeFromSection(("masa0286",))
    assert n is not None
    assert api.T.text(n, fmt="text-orig-full").strip() == ""
    assert api.T.text(n, fmt="text-orig-refs-full") == "((phoen-gaml))((phoen-delt))"
    synthetic = [
        s for s in api.L.d(n, otype="sign")
        if api.F.synthetic_kind.v(s) == "glyph_ref"
    ]
    assert len(synthetic) == 2
    assert all(api.F.glyph.v(s) is None for s in synthetic)
    assert all(api.F.primary_glyph.v(s) is None for s in synthetic)
    assert [
        api.F.ref.v(m)
        for m in api.L.d(n, otype="markup")
        if api.F.kind.v(m) == "glyph"
    ] == ["phoen-gaml", "phoen-delt"]


def test_mixed_content_does_not_duplicate_nonempty_glyphs(glyph_api: Any) -> None:
    n = glyph_api.T.nodeFromSection(("mixed",))
    assert n is not None
    assert glyph_api.T.text(n, fmt="text-orig-full") == "AB+C"
    assert glyph_api.T.text(n, fmt="text-orig-refs-full") == "A((phoen-gaml))B+C"


def test_selection_follows_normalized_choice_and_diplomatic_fallback(glyph_api: Any) -> None:
    branch = glyph_api.T.nodeFromSection(("branch",))
    dipl = glyph_api.T.nodeFromSection(("dipl",))
    assert branch is not None and dipl is not None
    assert glyph_api.T.text(branch, fmt="text-orig-full") == "y"
    assert glyph_api.T.text(branch, fmt="text-orig-refs-full") == "y((bird))"
    assert glyph_api.T.text(dipl, fmt="text-orig-full") == "Z"
    assert glyph_api.T.text(dipl, fmt="text-orig-refs-full") == "((phoen-wau))Z"


def test_reference_token_is_escaped_without_changing_source_ref(glyph_api: Any) -> None:
    n = glyph_api.T.nodeFromSection(("danger",))
    assert n is not None
    rendered = glyph_api.T.text(n, fmt="text-orig-refs-full")
    assert "<script>" not in rendered
    assert "((&lt;script&gt;))Q" == rendered
    marked = [
        m for m in glyph_api.L.d(n, otype="markup")
        if glyph_api.F.kind.v(m) == "glyph"
    ]
    assert len(marked) == 1
    assert glyph_api.F.ref.v(marked[0]) == "<script>"


def test_ambiguous_native_glyph_ref_fails_closed(
    tmp_path: Path
) -> None:
    from dataclasses import replace

    from iip_tf.ir import IRNode

    path = _source(tmp_path, "ambig", '<g ref="one"/>')
    ir = parse_epidoc_file(path, source_revision="fixture-revision")
    glyph = next(n for n in ir.nodes if n.feature("kind") == "glyph")
    extra = IRNode(
        key="ambig#duplicate-glyph",
        node_type=glyph.node_type,
        sign_keys=glyph.sign_keys,
        features=(("kind", "glyph"), ("ref", "two")),
    )
    ambiguous = replace(ir, nodes=(*ir.nodes, extra))
    with pytest.raises(TFWriterError, match="ambiguous glyph reference"):
        write_tf_corpus((ambiguous,), tmp_path / "fail", converter_commit="fixture-commit")


def test_schema_reference_labels_opt_in_not_source_reading() -> None:
    root = Path(__file__).resolve().parents[1]
    documentation = (root / "docs/reference/schema-0.1.md").read_text(
        encoding="utf-8"
    )
    assert "text-orig-refs-full" in documentation
    assert "((ref))" in documentation
    assert "not attested" in documentation.lower()
