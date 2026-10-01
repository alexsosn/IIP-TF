from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.ir import EdgeType, InscriptionIR, IRNode
from iip_tf.metadata_parser import MetadataParseError
from iip_tf.text_parser import parse_epidoc_file


def _write(path: Path, name: str, body: str) -> Path:
    target = path / name
    target.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><physDesc>'
        '<objectDesc><supportDesc><support>'
        + body
        + '</support></supportDesc></objectDesc>'
        '</physDesc></msDesc></sourceDesc></fileDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>'
        '</TEI>',
        encoding="utf-8",
    )
    return target


def _nodes(ir: InscriptionIR, node_type: str) -> list[IRNode]:
    return [node for node in ir.nodes if node.node_type.value == node_type]


@pytest.mark.parametrize(
    ("name", "first", "second"),
    [
        (
            "huld0001.xml",
            "Inscription inside a framed section of mosaic. Frame also includes decorations.",
            "Frame Measurments: 91x52 cm",
        ),
        (
            "huld0002.xml",
            "Inscription inside a mosaic circle.",
            "Dimensions provided are the diameter of the circle",
        ),
        (
            "kqaz0001.xml",
            "White-yellowish sandstone, tapering at the top",
            "35 cm x 12 cm at the bottom",
        ),
        (
            "tibr0002.xml",
            "Inscription inside a wreath.",
            "Inner diameter of the wreath: 52 cm.",
        ),
    ],
)
def test_repeated_support_paragraphs_become_independent_nodes(
    tmp_path: Path,
    name: str,
    first: str,
    second: str,
) -> None:
    path = _write(
        tmp_path,
        name,
        f"<p>{first}</p><dimensions type=\"surface\"/><p>{second}</p>",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    notes = _nodes(ir, "support_note")
    inscription = _nodes(ir, "inscription")[0]

    assert [node.feature("note") for node in notes] == [first, second]
    assert inscription.feature("support_note") is None
    assert notes[0].feature("source_key") != notes[1].feature("source_key")
    assert all(
        any(
            edge.edge_type == EdgeType.PARENT
            and edge.source == note.key
            and edge.target == inscription.key
            for edge in ir.edges
        )
        for note in notes
    )


def test_nested_surface_preserves_immediate_surface_parent(tmp_path: Path) -> None:
    path = tmp_path / "mgha0001.xml"
    path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <facsimile>
    <surface>
      <desc>Left side.</desc><graphic url="mgha0001b.jpg"/>
      <surface>
        <desc>Right side.</desc><graphic url="mgha0001c.pg"/>
      </surface>
    </surface>
  </facsimile>
  <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
</TEI>""",
        encoding="utf-8",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    surfaces = _nodes(ir, "facsimile_surface")
    images = _nodes(ir, "image")

    assert len(surfaces) == 2
    outer = next(node for node in surfaces if node.feature("description") == "Left side.")
    inner = next(node for node in surfaces if node.feature("description") == "Right side.")
    inner_image = next(node for node in images if node.feature("url") == "mgha0001c.pg")

    assert any(
        edge.edge_type == EdgeType.PARENT
        and edge.source == inner.key
        and edge.target == outer.key
        for edge in ir.edges
    )
    assert any(
        edge.edge_type == EdgeType.PARENT
        and edge.source == inner_image.key
        and edge.target == inner.key
        for edge in ir.edges
    )


def test_surface_depth_beyond_frozen_contract_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "deep.xml"
    path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <facsimile><surface><surface><surface><graphic url="x.jpg"/></surface></surface></surface></facsimile>
  <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
</TEI>""",
        encoding="utf-8",
    )

    with pytest.raises(MetadataParseError, match="surface depth"):
        parse_epidoc_file(path, source_revision="deadbeef")
