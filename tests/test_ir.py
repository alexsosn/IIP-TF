from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

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


def test_ir_is_immutable_and_contains_explicit_graph_primitives() -> None:
    sign = IRSign(key="x#s1", glyph="Α", layer=Layer.TRANSCRIPTION)
    node = IRNode(
        key="x#n1",
        node_type=NodeType.MARKUP,
        sign_keys=("x#s1",),
        features=(("kind", "unclear"),),
    )
    parent = IRNode(
        key="x#p1",
        node_type=NodeType.PARAGRAPH,
        sign_keys=("x#s1",),
    )
    edge = IREdge(edge_type=EdgeType.PARENT, source="x#n1", target="x#p1")
    ir = InscriptionIR(
        identity=SourceIdentity(
            inscription_id="x",
            source_file="x.xml",
            xml_id="x",
            iip_ids=("X 1",),
            main_lang="grc",
        ),
        provenance=SourceProvenance(
            source_revision="deadbeef",
            repaired=False,
            repair_id=None,
            conflict_count=0,
        ),
        signs=(sign,),
        nodes=(node, parent),
        edges=(edge,),
        diagnostics=(),
    )

    assert ir.sign("x#s1") == sign
    assert ir.node("x#n1") == node
    assert not hasattr(sign, "raw_xml")
    assert not hasattr(node, "raw_xml")

    with pytest.raises(FrozenInstanceError):
        sign.glyph = "Β"  # type: ignore[misc]


def test_ir_rejects_duplicate_keys_and_unknown_edge_targets() -> None:
    sign = IRSign(key="x#s1", glyph="Α", layer=Layer.TRANSCRIPTION)
    identity = SourceIdentity("x", "x.xml", "x", (), "grc")
    provenance = SourceProvenance("deadbeef", False, None, 0)

    with pytest.raises(ValueError, match="duplicate sign key"):
        InscriptionIR(identity, provenance, (sign, sign), (), (), ())

    edge = IREdge(EdgeType.PARENT, "x#missing", "x#also-missing")
    with pytest.raises(ValueError, match="unknown edge"):
        InscriptionIR(identity, provenance, (sign,), (), (edge,), ())
