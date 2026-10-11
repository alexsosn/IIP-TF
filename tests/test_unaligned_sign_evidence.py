"""#92 RED: inspect *source-evidence absence*, never infer sign language."""

from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.ir import (
    IRNode,
    IRSign,
    InscriptionIR,
    Layer,
    NodeType,
    SourceIdentity,
    SourceProvenance,
)
from iip_tf.language_audit import AramaicLanguageAudit
from iip_tf.text_parser import parse_epidoc_file


def _sign(key: str, *, layer: Layer = Layer.TRANSCRIPTION) -> IRSign:
    return IRSign(
        key, "א", layer, "heb", "inherited",
        lang_original="heb", lang_origin="div",
    )


def _candidate(
    index: int, selected: int, token_count: int, *,
    status: str = "single",
) -> IRNode:
    return IRNode(
        key=f"seg{index}", node_type=NodeType.SEGMENTATION, sign_keys=(),
        features=(
            ("candidate_index", index), ("selected", selected),
            ("token_count", token_count), ("resolution_status", status),
        ),
    )


def _word(
    key: str, signs: tuple[str, ...], *,
    status: str = "projected",
    lang: str = "arc", source_id: str = "source-token",
) -> IRNode:
    return IRNode(
        key=key, node_type=NodeType.WORD, sign_keys=signs,
        features=(
            ("candidate_index", 0), ("segmentation_status", status),
            ("lang", lang), ("lang_source", "transcription_segmented"),
            ("source_id", source_id), ("source_key", f"fixture#path:{source_id}"),
        ),
    )


def _ir(
    name: str,
    signs: tuple[IRSign, ...],
    nodes: tuple[IRNode, ...] = (),
    *,
    main_lang: str = "arc",
) -> InscriptionIR:
    return InscriptionIR(
        identity=SourceIdentity(name, f"{name}.xml", name, (), main_lang),
        provenance=SourceProvenance("fixture", False, None, 0),
        signs=signs, nodes=nodes, edges=(), diagnostics=(),
    )


def test_audit_partition_source_candidate_states_and_strict_reconciliation() -> None:
    cases = (
        ("absent", (), "no_segmented_edition"),
        ("unselected", (_candidate(0, 0, 0, status="all_empty"),),
         "no_selected_candidate"),
        ("zero", (_candidate(0, 1, 0),), "selected_zero_tokens"),
        ("no-words", (_candidate(0, 1, 1),), "selected_tokens_without_projected_words"),
        ("uncovered", (_candidate(0, 1, 1), _word("word", ("other",))),
         "selected_words_do_not_cover_sign"),
    )
    audit = AramaicLanguageAudit(max_examples=1)
    for record, nodes, _ in cases:
        sign = _sign(f"{record}-sign")
        other = _sign("other", layer=Layer.DIPLOMATIC)
        audit.ingest(_ir(record, (sign, other), nodes))
    result = audit.report()
    assert result["reasons"] == {"no_selected_word": 5}
    evidence = result["no_selected_word_evidence"]
    assert evidence["signs"] == 5
    assert evidence["reasons"] == {reason: 1 for _, _, reason in cases}
    assert sum(evidence["reasons"].values()) == result["reasons"]["no_selected_word"]
    assert evidence["records_with_unaligned"] == 5
    assert evidence["most_affected_records"] == [
        {"record": "absent", "signs": 1},
        {"record": "no-words", "signs": 1},
        {"record": "uncovered", "signs": 1},
        {"record": "unselected", "signs": 1},
        {"record": "zero", "signs": 1},
    ]
    assert all(len(samples) <= 1 for samples in evidence["examples"].values())
    assert result == audit.report()


def test_multiple_covered_signs_do_not_overflow_bounded_examples() -> None:
    audit = AramaicLanguageAudit(max_examples=2)
    audit.ingest(_ir("all", tuple(_sign(f"sign{i}") for i in range(5))))
    report = audit.report()["no_selected_word_evidence"]
    assert report["signs"] == 5
    assert report["reasons"] == {"no_segmented_edition": 5}
    assert [v["sign_key"] for v in report["examples"]["no_segmented_edition"]] == [
        "sign0", "sign1"
    ]


@pytest.mark.parametrize("selected", [2, -1, "1"])
def test_selected_candidate_value_must_be_integer_binary(selected: object) -> None:
    candidate = IRNode(
        key="bad", node_type=NodeType.SEGMENTATION,
        sign_keys=(),
        features=(("selected", selected), ("token_count", 2)),  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="selected"):
        AramaicLanguageAudit().ingest(_ir("invalid", (_sign("a"),), (candidate,)))


def test_duplicate_selected_candidates_fail_closed() -> None:
    with pytest.raises(ValueError, match="multiple|duplicate"):
        AramaicLanguageAudit().ingest(_ir(
            "duplicate", (_sign("a"),),
            (_candidate(0, 1, 2), _candidate(1, 1, 2)),
        ))


def test_negative_token_count_fails_closed() -> None:
    with pytest.raises(ValueError, match="token_count"):
        AramaicLanguageAudit().ingest(_ir(
            "invalid-count", (_sign("a"),), (_candidate(0, 1, -1),),
        ))


def test_drift_source_identity_is_reported_but_not_relabelled() -> None:
    sign = _sign("s")
    audit = AramaicLanguageAudit()
    audit.ingest(_ir(
        "driftcase", (sign,), (
            _candidate(0, 1, 1),
            _word(
                "w", ("s",), status="projected_with_source_drift",
                source_id="idum0375-8",
            ),
        ),
    ))
    result = audit.report()
    assert result["reasons"] == {"drift_or_uncertain_word_overlap": 1}
    assert result["no_selected_word_evidence"]["signs"] == 0
    assert result["drift_source_evidence"] == [
        {
            "record": "driftcase", "sign_key": "s", "glyph": "א",
            "words": [{
                "source_id": "idum0375-8",
                "source_key": "fixture#path:idum0375-8",
                "status": "projected_with_source_drift",
                "lang": "arc",
            }],
        }
    ]
    assert sign.lang == "heb"


def test_actual_parser_absent_vs_selected_coverage(tmp_path: Path) -> None:
    def source(name: str, segmented: str) -> Path:
        file = tmp_path / f"{name}.xml"
        file.write_text(
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
            '<textLang mainLang="arc"/></msContents></msDesc></sourceDesc>'
            '</fileDesc></teiHeader><text><body>'
            '<div type="edition" subtype="transcription" xml:lang="heb">'
            '<p>אב</p></div>' + segmented + '</body></text></TEI>',
            encoding="utf-8",
        )
        return file

    absent = parse_epidoc_file(source("absent", ""), source_revision="fixture")
    selected = parse_epidoc_file(source(
        "selected",
        '<div type="edition" subtype="transcription_segmented"><p>'
        '<w xml:id="selected-w" xml:lang="arc">א</w></p></div>',
    ), source_revision="fixture")
    audit = AramaicLanguageAudit()
    audit.ingest(absent)
    audit.ingest(selected)
    result = audit.report()
    assert result["reasons"]["no_selected_word"] == 3
    assert result["no_selected_word_evidence"]["reasons"] == {
        "no_segmented_edition": 2,
        "selected_words_do_not_cover_sign": 1,
    }
    assert result["corrected_signs"] == 1


def test_non_aramaic_and_diplomatic_signs_are_not_included() -> None:
    audit = AramaicLanguageAudit()
    audit.ingest(_ir("hebrew", (_sign("h"),), main_lang="hbo"))
    audit.ingest(_ir("diplomatic", (_sign("d", layer=Layer.DIPLOMATIC),)))
    assert audit.report()["no_selected_word_evidence"]["signs"] == 0
