"""Issue #54-D RED: classify residual Aramaic transcription language conservatively."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iip_tf.ir import (
    InscriptionIR,
    IRNode,
    IRSign,
    Layer,
    NodeType,
    SourceIdentity,
    SourceProvenance,
)
from iip_tf.language_audit import AramaicLanguageAudit
from iip_tf.text_parser import parse_epidoc_file


def _sign(
    key: str,
    glyph: str,
    *,
    lang: str = "heb",
    origin: str = "p",
    original: str = "heb",
    source: str = "inherited",
    synthetic_kind: str | None = None,
    layer: Layer = Layer.TRANSCRIPTION,
) -> IRSign:
    return IRSign(
        key=key, glyph=glyph, layer=layer, lang=lang,
        lang_source=source, lang_original=original,
        lang_origin=origin, synthetic_kind=synthetic_kind,
    )


def _word(
    key: str, keys: tuple[str, ...], *,
    lang: str | None = "arc", status: str = "projected",
) -> IRNode:
    features: list[tuple[str, str]] = [
        ("lang_source", "transcription_segmented"),
        ("segmentation_status", status),
    ]
    if lang is not None:
        features.append(("lang", lang))
    return IRNode(
        key=key, node_type=NodeType.WORD,
        sign_keys=keys, features=tuple(features),
    )


def _ir(
    signs: tuple[IRSign, ...],
    words: tuple[IRNode, ...] = (),
    *,
    id: str = "fixture",
    main_lang: str = "arc",
) -> InscriptionIR:
    return InscriptionIR(
        identity=SourceIdentity(id, f"{id}.xml", id, (), main_lang),
        provenance=SourceProvenance("fixture-pin", False, None, 0),
        signs=signs, nodes=words, edges=(), diagnostics=(),
    )


def test_residual_reason_partition_has_no_double_counting() -> None:
    signs = (
        _sign("corrected", "א", lang="arc", source="transcription_segmented"),
        _sign("no-word", "ב"),
        _sign("other-word", "ג"),
        _sign("without-lang", "ד"),
        _sign("drift-overlap", "ה"),
        _sign("foreign", "ו", origin="foreign"),
        _sign("source-not-heb", "ז", original="he"),
        _sign("non-hebrew", "β"),
        _sign("nonletter", ","),
        _sign("technical", "", synthetic_kind="line_break"),
        _sign("diplomatic", "ח", layer=Layer.DIPLOMATIC),
    )
    words = (
        _word("w0", ("corrected",)),
        _word("w1", ("other-word",), lang="grc"),
        _word("w2", ("without-lang",), lang=None),
        _word("w3", ("drift-overlap",)),
        _word("w4", ("drift-overlap",), status="projected_with_source_drift"),
        _word("w5", ("foreign",)),
    )
    audit = AramaicLanguageAudit(max_examples=1)
    audit.ingest(_ir(signs, words))
    report = audit.report()

    assert report["records_scanned"] == 1
    assert report["corrected_signs"] == 1
    assert report["remaining_signs"] == 9
    assert report["reasons"] == {
        "no_selected_word": 1,
        "selected_non_arc_word": 1,
        "selected_word_without_lang": 1,
        "drift_or_uncertain_word_overlap": 1,
        "non_paragraph_source": 1,
        "source_label_not_heb": 1,
        "non_hebrew_encoded_letter": 1,
        "nonletter": 1,
        "synthetic": 1,
    }
    assert sum(report["reasons"].values()) == report["remaining_signs"]
    assert all(len(rows) <= 1 for rows in report["examples"].values())
    assert report["most_affected_records"] == [
        {"record": "fixture", "remaining_signs": 9}
    ]
    assert "diplomatic" not in json.dumps(report)
    assert report == audit.report(), "report ordering and sample selection must be stable"


def test_clean_arc_still_heb_is_a_hard_failure() -> None:
    audit = AramaicLanguageAudit()
    with pytest.raises(ValueError, match="still.*heb|arc.*heb"):
        audit.ingest(_ir((_sign("bad", "א"),), (_word("w", ("bad",)),)))


def test_corrected_word_must_be_supported_and_not_overlap_source_drift() -> None:
    corrected = _sign(
        "bad", "א", lang="arc", source="transcription_segmented"
    )
    with pytest.raises(ValueError, match="corrected.*without"):
        AramaicLanguageAudit().ingest(_ir((corrected,)))
    with pytest.raises(ValueError, match="drift|uncertain"):
        AramaicLanguageAudit().ingest(_ir(
            (corrected,),
            (
                _word("clean", ("bad",)),
                _word("drift", ("bad",), status="projected_with_source_drift"),
            ),
        ))


def test_unrelated_record_and_nonprimary_layer_are_not_counted() -> None:
    report = AramaicLanguageAudit()
    report.ingest(_ir((_sign("x", "א"),), main_lang="he", id="hebrew"))
    report.ingest(_ir((_sign("d", "א", layer=Layer.DIPLOMATIC),), id="aramaic"))
    assert report.report()["remaining_signs"] == 0
    assert report.report()["corrected_signs"] == 0
    assert report.report()["records_scanned"] == 1


def test_real_parser_projected_word_and_unsegmented_paragraph(tmp_path: Path) -> None:
    def make(name: str, *, words: bool) -> Path:
        path = tmp_path / f"{name}.xml"
        segmented = (
            '<div type="edition" subtype="transcription_segmented">'
            '<p><w xml:id="' + name + '-w1" xml:lang="arc">אב</w> '
            '<w xml:id="' + name + '-w2" xml:lang="he">גד</w></p></div>'
            if words else ""
        )
        path.write_text(
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
            '<textLang mainLang="arc"/></msContents></msDesc></sourceDesc>'
            '</fileDesc></teiHeader><text><body>'
            '<div type="edition" subtype="transcription">'
            '<p xml:lang="heb">אב גד</p></div>'
            + segmented + '</body></text></TEI>',
            encoding="utf-8",
        )
        return path

    audit = AramaicLanguageAudit()
    audit.ingest(parse_epidoc_file(make("words", words=True), source_revision="fixture"))
    audit.ingest(parse_epidoc_file(make("bare", words=False), source_revision="fixture"))
    report = audit.report()
    assert report["corrected_signs"] == 2
    assert report["remaining_signs"] == 6
    assert report["reasons"] == {
        "no_selected_word": 4, "selected_non_arc_word": 2
    }
    assert report["most_affected_records"][0]["record"] == "bare"
    assert report["most_affected_records"][0]["remaining_signs"] == 4
