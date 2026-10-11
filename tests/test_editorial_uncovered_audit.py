"""#94 RED: editorial siblings are not automatically aligned or same-language."""

from __future__ import annotations

from pathlib import Path

from iip_tf.ir import (
    EdgeType,
    InscriptionIR,
    IREdge,
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
    key: str, *,
    role: str = "both",
    lang: str = "heb",
    glyph: str = "א",
) -> IRSign:
    return IRSign(
        key=key, glyph=glyph, layer=Layer.TRANSCRIPTION,
        lang=lang, lang_source=(
            "transcription_segmented" if lang == "arc" else "inherited"
        ),
        lang_original="heb", lang_origin="p", reading_role=role,
    )


def _node(key: str, kind: str, keys: tuple[str, ...]) -> IRNode:
    return IRNode(key=key, node_type=NodeType.MARKUP, sign_keys=keys,
                  features=(("kind", kind),))


def _word(keys: tuple[str, ...], *, source_id: str = "orig-1") -> IRNode:
    return IRNode(
        key=f"word-{source_id}", node_type=NodeType.WORD, sign_keys=keys,
        features=(
            ("candidate_index", 0), ("segmentation_status", "projected"),
            ("source_id", source_id), ("lang", "arc"),
            ("lang_source", "transcription_segmented"),
        ),
    )


def _candidate() -> IRNode:
    return IRNode(
        key="seg", node_type=NodeType.SEGMENTATION, sign_keys=(),
        features=(("candidate_index", 0), ("selected", 1), ("token_count", 1)),
    )


def _ir(
    name: str,
    signs: tuple[IRSign, ...],
    nodes: tuple[IRNode, ...],
    edges: tuple[IREdge, ...] = (),
) -> InscriptionIR:
    return InscriptionIR(
        identity=SourceIdentity(name, f"{name}.xml", name, (), "arc"),
        provenance=SourceProvenance("fixture", False, None, 0),
        signs=signs, nodes=nodes, edges=edges, diagnostics=(),
    )


def _editorial_case(
    name: str, *,
    parent: str, covered: str, uncovered: str,
    covered_role: str = "source", uncovered_role: str = "normalized",
) -> InscriptionIR:
    signs = (
        _sign("s1", role=covered_role, lang="arc"),
        _sign("s2", role=uncovered_role),
    )
    parent_node = _node("container", parent, ("s1", "s2"))
    branches = (
        _node("source-branch", covered, ("s1",)),
        _node("other-branch", uncovered, ("s2",)),
    )
    edges = (
        IREdge(EdgeType.PARENT, "source-branch", "container"),
        IREdge(EdgeType.PARENT, "other-branch", "container"),
    )
    return _ir(name, signs, (_candidate(), parent_node, *branches,
                             _word(("s1",))), edges)


def test_orig_reg_sibling_token_is_reported_without_relabelling() -> None:
    ir = _editorial_case("origreg", parent="choice",
                         covered="orig", uncovered="reg")
    before = ir.sign("s2")
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    data = audit.report()["selected_uncovered_editorial_evidence"]
    assert data["signs"] == 1
    assert data["reading_roles"] == {"normalized": 1}
    assert data["markup_branches"] == {"reg": 1}
    assert data["alternate_branch_has_projected_word"] == 1
    assert data["examples"][0] == {
        "record": "origreg", "sign_key": "s2", "glyph": "א",
        "reading_role": "normalized", "markup_branch": "reg",
        "editorial_container": "choice",
        "alternate_branch_has_projected_word": True,
        "alternate_source_id": "orig-1",
    }
    assert ir.sign("s2") == before
    assert before.lang == "heb"


def test_apparatus_lem_rdg_sibling_is_not_a_sign_language_override() -> None:
    ir = _editorial_case("apparatus", parent="apparatus", covered="lem",
                         uncovered="rdg", covered_role="both",
                         uncovered_role="both")
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    result = audit.report()["selected_uncovered_editorial_evidence"]
    assert result["reading_roles"] == {"both": 1}
    assert result["markup_branches"] == {"rdg": 1}
    assert result["alternate_branch_has_projected_word"] == 1
    assert result["examples"][0]["editorial_container"] == "apparatus"


def test_selected_word_elsewhere_in_paragraph_is_not_sibling_evidence() -> None:
    signs = (_sign("s1", lang="arc"), _sign("s2"))
    ir = _ir("elsewhere", signs, (_candidate(), _word(("s1",))))
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    result = audit.report()["selected_uncovered_editorial_evidence"]
    assert result["signs"] == 1
    assert result["reading_roles"] == {"both": 1}
    assert result["markup_branches"] == {"none": 1}
    assert result["alternate_branch_has_projected_word"] == 0


def test_multiple_records_and_examples_are_reconciled_and_bounded() -> None:
    audit = AramaicLanguageAudit(max_examples=1)
    audit.ingest(_editorial_case("a", parent="choice",
                                covered="orig", uncovered="reg"))
    audit.ingest(_editorial_case("b", parent="choice",
                                covered="sic", uncovered="corr"))
    data = audit.report()["selected_uncovered_editorial_evidence"]
    assert data["signs"] == 2
    assert data["reading_roles"] == {"normalized": 2}
    assert data["markup_branches"] == {"corr": 1, "reg": 1}
    assert data["alternate_branch_has_projected_word"] == 2
    assert len(data["examples"]) == 1
    assert data["examples"][0]["record"] == "a"
    assert data["most_affected_records"] == [
        {"record": "a", "signs": 1}, {"record": "b", "signs": 1}
    ]
    assert data == audit.report()["selected_uncovered_editorial_evidence"]


def test_actual_epidoc_orig_reg_role_and_word_projection(tmp_path: Path) -> None:
    path = tmp_path / "editorial.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        '<textLang mainLang="arc"/></msContents></msDesc></sourceDesc>'
        '</fileDesc></teiHeader><text><body>'
        '<div type="edition" subtype="transcription">'
        '<p xml:lang="heb"><choice><orig>אב</orig><reg>גב</reg></choice></p>'
        '</div><div type="edition" subtype="transcription_segmented">'
        '<p><orig xml:id="editorial-orig" xml:lang="arc">אב</orig></p>'
        '</div></body></text></TEI>', encoding="utf-8",
    )
    ir = parse_epidoc_file(path, source_revision="fixture")
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    data = audit.report()["selected_uncovered_editorial_evidence"]
    assert data["signs"] == 2
    assert data["reading_roles"] == {"normalized": 2}
    assert data["markup_branches"] == {"reg": 2}
    assert data["alternate_branch_has_projected_word"] == 2
    assert all(
        sign.lang == "heb" and sign.lang_original == "heb"
        for sign in ir.signs if sign.reading_role == "normalized"
        and sign.glyph
    )
