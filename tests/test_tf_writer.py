from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

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
from iip_tf.tf_writer import TFWriterError, write_tf_corpus


REVISION = "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"
CONVERTER_COMMIT = "deadbeef"


def _record(record_id: str = "demo") -> InscriptionIR:
    signs = (
        IRSign(f"{record_id}#s1", "A", Layer.TRANSCRIPTION, reading_role="both", after=" "),
        IRSign(f"{record_id}#s2", "x", Layer.TRANSCRIPTION, reading_role="source"),
        IRSign(
            f"{record_id}#s3",
            "y",
            Layer.TRANSCRIPTION,
            reading_role="normalized",
            after=" ",
        ),
        IRSign(f"{record_id}#s4", "B", Layer.TRANSCRIPTION, reading_role="both"),
    )
    inscription = IRNode(
        key=f"{record_id}#record",
        node_type=NodeType.INSCRIPTION,
        sign_keys=tuple(sign.key for sign in signs),
        features=(
            ("inscription_id", record_id),
            ("source_file", f"{record_id}.xml"),
            ("primary_layer", "transcription"),
        ),
    )
    textpart = IRNode(
        key=f"{record_id}#textpart",
        node_type=NodeType.TEXTPART,
        sign_keys=tuple(sign.key for sign in signs),
        features=(("layer", "transcription"), ("section_part", "transcription")),
    )
    line = IRNode(
        key=f"{record_id}#line",
        node_type=NodeType.LINE,
        sign_keys=tuple(sign.key for sign in signs),
        features=(("layer", "transcription"), ("line_n", 1)),
    )
    word = IRNode(
        key=f"{record_id}#word",
        node_type=NodeType.WORD,
        sign_keys=tuple(sign.key for sign in signs),
        features=(("word_text", "demo-word"), ("token_id", "demo-1")),
    )
    point = IRNode(
        key=f"{record_id}#point",
        node_type=NodeType.MARKUP,
        sign_keys=(),
        features=(("kind", "unclear"), ("layer", "transcription")),
        point_index=3,
    )
    empty = IRNode(
        key=f"{record_id}#empty-p",
        node_type=NodeType.PARAGRAPH,
        sign_keys=(),
        features=(("kind", "p"), ("layer", "commentary")),
    )
    nodes = (inscription, textpart, line, word, point, empty)
    edges = (
        IREdge(EdgeType.PARENT, textpart.key, inscription.key),
        IREdge(EdgeType.PARENT, line.key, textpart.key),
        IREdge(EdgeType.PARENT, point.key, textpart.key),
        IREdge(EdgeType.PARENT, empty.key, inscription.key),
    )
    return InscriptionIR(
        identity=SourceIdentity(
            inscription_id=record_id,
            source_file=f"{record_id}.xml",
            xml_id=record_id,
            iip_ids=(record_id,),
            main_lang="grc",
        ),
        provenance=SourceProvenance(REVISION, False, None, 0),
        signs=signs,
        nodes=nodes,
        edges=edges,
        diagnostics=(),
    )


def _empty_record(record_id: str = "empty") -> InscriptionIR:
    sign = IRSign(
        f"{record_id}#s1",
        "",
        Layer.ANCHOR,
        synthetic_kind="anchor",
    )
    inscription = IRNode(
        key=f"{record_id}#record",
        node_type=NodeType.INSCRIPTION,
        sign_keys=(sign.key,),
        features=(
            ("inscription_id", record_id),
            ("source_file", f"{record_id}.xml"),
            ("primary_layer", "empty"),
        ),
    )
    edition = IRNode(
        key=f"{record_id}#edition",
        node_type=NodeType.EDITION,
        sign_keys=(),
        features=(("layer", "transcription"), ("edition_kind", "transcription"), ("empty", "1")),
    )
    return InscriptionIR(
        identity=SourceIdentity(record_id, f"{record_id}.xml", record_id, (), None),
        provenance=SourceProvenance(REVISION, False, None, 0),
        signs=(sign,),
        nodes=(inscription, edition),
        edges=(IREdge(EdgeType.PARENT, edition.key, inscription.key),),
        diagnostics=(),
    )


def _load(path: Path) -> Any:
    api = Fabric(locations=str(path), silent=True).loadAll(silent=True)
    assert api
    return api


def _tf_files(path: Path) -> dict[str, bytes]:
    return {
        item.name: item.read_bytes()
        for item in sorted(path.glob("*.tf"))
    }


def test_writer_round_trips_warp_edges_points_empty_nodes_and_formats(tmp_path: Path) -> None:
    output = tmp_path / "tf"
    write_tf_corpus((_record(), _empty_record()), output, converter_commit=CONVERTER_COMMIT)

    api = _load(output)
    F = api.F
    E = api.E
    L = api.L
    T = api.T

    demo = F.inscription_id.s("demo")[0]
    assert T.text(demo, fmt="text-orig-full") == "A y B"
    assert T.text(demo, fmt="text-source-full") == "A x B"
    assert T.text(demo, fmt="text-transcription-full") == "A y B"

    word = F.token_id.s("demo-1")[0]
    assert T.text(word) == "demo-word"
    assert T.text(word, fmt="word-default") == "demo-word"

    point = F.kind.s("unclear")[0]
    point_slots = L.d(point, otype="sign")
    assert len(point_slots) == 1
    assert F.glyph.v(point_slots[0]) == "B"
    assert F.point_index.v(point) == 3
    assert F.point_relation.v(point) == "before"

    empty_paragraph = next(
        node
        for node in F.otype.s("paragraph")
        if F.kind.v(node) == "p" and F.layer.v(node) == "commentary"
    )
    assert F.empty.v(empty_paragraph) == "1"
    assert tuple(L.d(empty_paragraph, otype="sign")) == (1,)

    textpart = F.otype.s("textpart")[0]
    assert point in E.parent.t(textpart)

    empty_inscription = F.inscription_id.s("empty")[0]
    assert T.sectionFromNode(empty_inscription)[0] == "empty"
    assert not any(
        F.section_part.v(node)
        for node in F.otype.s("textpart")
        if empty_inscription in api.L.u(node, otype="inscription")
    )


def test_writer_output_is_byte_stable_and_removes_date_written(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    irs = (_record(), _empty_record())

    write_tf_corpus(irs, first, converter_commit=CONVERTER_COMMIT)
    write_tf_corpus(tuple(reversed(irs)), second, converter_commit=CONVERTER_COMMIT)

    assert _tf_files(first) == _tf_files(second)
    assert _tf_files(first)
    for content in _tf_files(first).values():
        assert b"@dateWritten=" not in content


def test_writer_fails_closed_on_duplicate_global_key(tmp_path: Path) -> None:
    first = _record("same")
    base = _record("other")
    old_inscription = base.nodes[0].key
    colliding = IRNode(
        key=first.nodes[0].key,
        node_type=NodeType.INSCRIPTION,
        sign_keys=base.nodes[0].sign_keys,
        features=base.nodes[0].features,
    )
    second = InscriptionIR(
        identity=base.identity,
        provenance=base.provenance,
        signs=base.signs,
        nodes=(colliding, *base.nodes[1:]),
        edges=tuple(
            IREdge(
                edge.edge_type,
                edge.source,
                colliding.key if edge.target == old_inscription else edge.target,
            )
            for edge in base.edges
        ),
        diagnostics=(),
    )
    with pytest.raises(TFWriterError, match="duplicate canonical key"):
        write_tf_corpus((first, second), tmp_path / "tf", converter_commit=CONVERTER_COMMIT)


def test_writer_fails_closed_on_wrong_feature_type(tmp_path: Path) -> None:
    ir = _record()
    bad = IRNode(
        key="demo#bad",
        node_type=NodeType.MARKUP,
        sign_keys=(ir.signs[0].key,),
        features=(("kind", "unclear"), ("candidate_index", "0")),
    )
    ir = InscriptionIR(
        identity=ir.identity,
        provenance=ir.provenance,
        signs=ir.signs,
        nodes=(*ir.nodes, bad),
        edges=ir.edges,
        diagnostics=ir.diagnostics,
    )
    with pytest.raises(TFWriterError, match="declared int domain"):
        write_tf_corpus((ir,), tmp_path / "tf", converter_commit=CONVERTER_COMMIT)


def test_writer_fails_closed_on_inconsistent_source_revision(tmp_path: Path) -> None:
    other = _record("other")
    other = InscriptionIR(
        identity=other.identity,
        provenance=SourceProvenance("future", False, None, 0),
        signs=other.signs,
        nodes=other.nodes,
        edges=other.edges,
        diagnostics=(),
    )
    with pytest.raises(TFWriterError, match="source revision"):
        write_tf_corpus((_record(), other), tmp_path / "tf", converter_commit=CONVERTER_COMMIT)


def test_writer_rejects_point_semantics_on_structural_node(tmp_path: Path) -> None:
    ir = _record()
    bad = IRNode(
        "demo#point-paragraph",
        NodeType.PARAGRAPH,
        (),
        features=(("kind", "p"), ("layer", "transcription")),
        point_index=1,
    )
    ir = InscriptionIR(
        identity=ir.identity,
        provenance=ir.provenance,
        signs=ir.signs,
        nodes=(*ir.nodes, bad),
        edges=ir.edges,
        diagnostics=ir.diagnostics,
    )
    with pytest.raises(TFWriterError, match="point semantics"):
        write_tf_corpus((ir,), tmp_path / "tf", converter_commit=CONVERTER_COMMIT)


def test_writer_rejects_unexpected_empty_node_type(tmp_path: Path) -> None:
    ir = _record()
    extra = IRNode("demo#empty-word", NodeType.WORD, (), features=(("word_text", ""),))
    ir = InscriptionIR(
        identity=ir.identity,
        provenance=ir.provenance,
        signs=ir.signs,
        nodes=(*ir.nodes, extra),
        edges=ir.edges,
        diagnostics=ir.diagnostics,
    )
    with pytest.raises(TFWriterError, match="empty semantic span"):
        write_tf_corpus((ir,), tmp_path / "tf", converter_commit=CONVERTER_COMMIT)
