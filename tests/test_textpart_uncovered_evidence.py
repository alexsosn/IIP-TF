"""#96 RED: source textpart coverage is not inscription-wide word evidence."""

from __future__ import annotations

from pathlib import Path

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


def _sign(key: str, *, lang: str = "heb", role: str = "both") -> IRSign:
    return IRSign(
        key=key, glyph="א", layer=Layer.TRANSCRIPTION, lang=lang,
        lang_source=("transcription_segmented" if lang == "arc" else "inherited"),
        lang_original="heb", lang_origin="p", reading_role=role,
    )


def _part(name: str, keys: tuple[str, ...], *, explicit: bool) -> IRNode:
    return IRNode(
        key=name, node_type=NodeType.TEXTPART, sign_keys=keys,
        features=(("section_part",
                   f"transcription:column:{name}" if explicit else "transcription"),
                  ("source_key", f"case#path:{name}")),
    )


def _word(keys: tuple[str, ...], *, kind: str = "w") -> IRNode:
    return IRNode(
        key="word", node_type=NodeType.WORD, sign_keys=keys,
        features=(
            ("candidate_index", 0), ("segmentation_status", "projected"),
            ("source_id", f"source-{kind}"), ("token_kind", kind),
            ("lang", "arc"), ("lang_source", "transcription_segmented"),
        ),
    )


def _ir(
    name: str, signs: tuple[IRSign, ...], nodes: tuple[IRNode, ...],
) -> InscriptionIR:
    seg = IRNode(
        key="candidate", node_type=NodeType.SEGMENTATION, sign_keys=(),
        features=(("candidate_index", 0), ("selected", 1), ("token_count", 1)),
    )
    return InscriptionIR(
        identity=SourceIdentity(name, f"{name}.xml", name, (), "arc"),
        provenance=SourceProvenance("fixture", False, None, 0),
        signs=signs, nodes=(seg, *nodes), edges=(), diagnostics=(),
    )


def test_selected_word_in_other_explicit_textpart_does_not_cover_sign() -> None:
    ir = _ir(
        "two-parts",
        (_sign("a", lang="arc"), _sign("b")),
        (
            _part("column-a", ("a",), explicit=True),
            _part("column-b", ("b",), explicit=True),
            _word(("a",)),
        ),
    )
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    result = audit.report()["selected_uncovered_textpart_evidence"]
    assert result["signs"] == 1
    assert result["scopes"] == {"explicit_without_selected_word": 1}
    assert result["token_kinds_in_sign_textpart"] == {}
    assert result["examples"][0]["section_part"] == "transcription:column:column-b"
    assert result["examples"][0]["sign_key"] == "b"


def test_same_explicit_textpart_selected_number_token_is_not_word_language() -> None:
    ir = _ir(
        "same-part",
        (_sign("a", lang="arc"), _sign("b", role="normalized")),
        (
            _part("part", ("a", "b"), explicit=True),
            _word(("a",), kind="num"),
        ),
    )
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    result = audit.report()["selected_uncovered_textpart_evidence"]
    assert result["scopes"] == {"explicit_with_selected_word": 1}
    assert result["token_kinds_in_sign_textpart"] == {"num": 1}
    assert result["normalized_no_editorial_examples"] == [
        {
            "record": "same-part", "sign_key": "b", "glyph": "א",
            "section_part": "transcription:column:part",
            "lang_original": "heb", "lang_origin": "p",
        }
    ]


def test_implicit_and_missing_textparts_are_reported_separately() -> None:
    audit = AramaicLanguageAudit(max_examples=1)
    audit.ingest(_ir("implicit", (_sign("a", lang="arc"), _sign("b")), (
        _part("i", ("a", "b"), explicit=False), _word(("a",)),
    )))
    audit.ingest(_ir("missing", (_sign("a", lang="arc"), _sign("b")), (
        _word(("a",)),
    )))
    evidence = audit.report()["selected_uncovered_textpart_evidence"]
    assert evidence["signs"] == 2
    assert evidence["scopes"] == {
        "implicit_with_selected_word": 1, "no_textpart": 1
    }
    assert evidence["most_affected_records"] == [
        {"record": "implicit", "signs": 1},
        {"record": "missing", "signs": 1},
    ]
    assert len(evidence["examples"]) == 1
    assert evidence == audit.report()["selected_uncovered_textpart_evidence"]


def test_actual_epidoc_separate_textparts_are_not_interchangeable(
    tmp_path: Path,
) -> None:
    source = tmp_path / "columns.xml"
    source.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        '<textLang mainLang="arc"/></msContents></msDesc></sourceDesc>'
        '</fileDesc></teiHeader><text><body>'
        '<div type="edition" subtype="transcription">'
        '<div type="textpart" subtype="column" n="a"><p xml:lang="heb">אב</p></div>'
        '<div type="textpart" subtype="column" n="b"><p xml:lang="heb">גד</p></div>'
        '</div><div type="edition" subtype="transcription_segmented"><p>'
        '<w xml:id="col-a" xml:lang="arc">אב</w>'
        '</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    ir = parse_epidoc_file(source, source_revision="fixture")
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    data = audit.report()["selected_uncovered_textpart_evidence"]
    assert data["signs"] == 2
    assert data["scopes"] == {"explicit_without_selected_word": 2}
    assert data["examples"][0]["section_part"] == "transcription:column:b"
    assert all(
        s.lang == "heb" for s in ir.signs
        if s.layer == Layer.TRANSCRIPTION and s.key in
        next(n.sign_keys for n in ir.nodes_of_type(NodeType.TEXTPART)
             if n.feature("section_part") == "transcription:column:b")
    )
