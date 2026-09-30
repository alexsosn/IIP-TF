# ruff: noqa: E501
from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode, Layer, NodeType
from iip_tf.text_parser import (
    UnsupportedTextualConstructError,
    parse_epidoc_file,
)


def _write(path: Path, name: str, text: str) -> Path:
    target = path / name
    target.write_text(text, encoding="utf-8")
    return target


def _nodes(ir: InscriptionIR, node_type: NodeType) -> list[IRNode]:
    return [node for node in ir.nodes if node.node_type == node_type]


def test_parse_transcription_preserves_signs_lines_and_zero_width_events(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "greek0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="greek0001">
  <teiHeader><fileDesc><publicationStmt><idno type="IIP">Greek 1</idno></publicationStmt>
  <sourceDesc><msDesc><msContents><textLang mainLang="grc"/></msContents></msDesc></sourceDesc>
  </fileDesc></teiHeader>
  <text><body>
    <div type="edition" subtype="transcription" xml:id="greek0001.transcription">
      <p>Α<supplied reason="lost">Β</supplied><lb/>Γ<gap reason="lost" unit="character" quantity="5"/></p>
    </div>
  </body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")

    assert ir.identity.inscription_id == "greek0001"
    assert ir.identity.main_lang == "grc"
    assert [sign.glyph for sign in ir.signs if sign.glyph] == ["Α", "Β", "Γ"]
    assert [sign.synthetic_kind for sign in ir.signs if sign.synthetic_kind] == [
        "line_break",
        "gap",
    ]
    assert sum(sign.synthetic_kind == "gap" for sign in ir.signs) == 1
    assert len(_nodes(ir, NodeType.LINE)) == 2
    assert len(_nodes(ir, NodeType.PARAGRAPH)) == 1
    assert len(_nodes(ir, NodeType.TEXTPART)) == 1
    assert ir.node_feature(NodeType.INSCRIPTION, "primary_layer") == "transcription"


def test_choice_and_expansion_preserve_all_branches_with_reading_roles(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "choice0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="choice0001">
  <teiHeader><fileDesc><sourceDesc><msDesc><msContents><textLang mainLang="grc"/></msContents></msDesc></sourceDesc></fileDesc></teiHeader>
  <text><body><div type="edition" subtype="transcription"><p>
    <choice><corr>Ε</corr><sic>ΑΙ</sic></choice>
    <expan><abbr>κ</abbr><ex>αί</ex></expan>
    <del>Χ</del><surplus>Ψ</surplus>
  </p></div></body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    by_glyph = {sign.glyph: sign.reading_role for sign in ir.signs if sign.glyph}

    assert by_glyph["Ε"] == "normalized"
    assert by_glyph["Α"] == "source"
    assert by_glyph["Ι"] == "source"
    assert by_glyph["κ"] == "both"
    assert by_glyph["α"] == "normalized"
    assert by_glyph["ί"] == "normalized"
    assert by_glyph["Χ"] == "source"
    assert by_glyph["Ψ"] == "source"

    kinds = {node.feature("kind") for node in _nodes(ir, NodeType.MARKUP)}
    assert {"choice", "corr", "sic", "expan", "abbr", "ex", "del", "surplus"} <= kinds


def test_translation_entities_keep_nested_spans_and_attributes(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "entity0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="entity0001">
  <teiHeader><fileDesc><sourceDesc><msDesc><msContents><textLang mainLang="grc"/></msContents></msDesc></sourceDesc></fileDesc></teiHeader>
  <text><body>
    <div type="edition" subtype="transcription"><p>Μαρία</p></div>
    <div type="translation" xml:id="entity0001.translation"><p>
      May <name type="patr"><persName ref="persons.xml#p1" xml:lang="grc ">Maria</persName></name>
      <rs type="formula" ana="interpretations.xml#memory"> be remembered</rs>.
    </p></div>
  </body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    entities = _nodes(ir, NodeType.ENTITY)

    person = next(node for node in entities if node.feature("entity_kind") == "person")
    assert person.feature("ref") == "persons.xml#p1"
    assert person.feature("lang") == "grc"
    assert ir.text(person.sign_keys) == "Maria"

    name = next(node for node in entities if node.feature("entity_kind") == "name")
    assert name.feature("entity_type") == "patr"
    assert set(person.sign_keys) <= set(name.sign_keys)


def test_diplomatic_fallback_and_empty_anchor_do_not_invent_text(tmp_path: Path) -> None:
    fallback = _write(
        tmp_path,
        "fallback.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="fallback"><text><body>
          <div type="edition" subtype="transcription"><p/></div>
          <div type="edition" subtype="diplomatic"><p>ABC</p></div>
        </body></text></TEI>""",
    )
    empty = _write(
        tmp_path,
        "empty.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="empty"><text><body>
          <div type="edition" subtype="transcription"><p/></div>
          <div type="translation"><p>Only translation</p></div>
        </body></text></TEI>""",
    )

    fallback_ir = parse_epidoc_file(fallback, source_revision="deadbeef")
    assert fallback_ir.node_feature(NodeType.INSCRIPTION, "primary_layer") == "diplomatic"
    assert any(sign.layer == Layer.DIPLOMATIC and sign.glyph == "A" for sign in fallback_ir.signs)

    empty_ir = parse_epidoc_file(empty, source_revision="deadbeef")
    assert empty_ir.node_feature(NodeType.INSCRIPTION, "primary_layer") == "empty"
    anchors = [sign for sign in empty_ir.signs if sign.synthetic_kind == "anchor"]
    assert len(anchors) == 1
    assert anchors[0].glyph == ""
    assert all(sign.layer != Layer.ANCHOR or not sign.glyph for sign in empty_ir.signs)


def test_explicit_textpart_language_and_whitespace_are_preserved_without_indentation(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "part0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="part0001">
  <teiHeader><fileDesc><sourceDesc><msDesc><msContents><textLang mainLang="grc"/></msContents></msDesc></sourceDesc></fileDesc></teiHeader>
  <text><body><div type="edition" subtype="transcription">
    <div type="textpart" subtype="reverse" n="2" xml:lang="heb">
      <p>אב <unclear>גד</unclear></p>
    </div>
  </div></body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")

    parts = _nodes(ir, NodeType.TEXTPART)
    assert len(parts) == 1
    assert parts[0].feature("source_n") == "2"
    assert parts[0].feature("subtype") == "reverse"
    assert parts[0].feature("section_part") == "transcription:reverse:2"
    assert ir.text(parts[0].sign_keys) == "אב גד"
    assert {sign.lang for sign in ir.signs if sign.glyph} == {"heb"}


def test_unknown_textual_constructs_and_attributes_fail_closed(tmp_path: Path) -> None:
    unknown_element = _write(
        tmp_path,
        "bad-element.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="bad"><text><body>
        <div type="edition" subtype="transcription"><p>A<seg>B</seg></p></div>
        </body></text></TEI>""",
    )
    unknown_attribute = _write(
        tmp_path,
        "bad-attribute.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="bad2"><text><body>
        <div type="edition" subtype="transcription"><p><supplied reason="lost" bogus="x">A</supplied></p></div>
        </body></text></TEI>""",
    )

    with pytest.raises(UnsupportedTextualConstructError, match="seg"):
        parse_epidoc_file(unknown_element, source_revision="deadbeef")

    with pytest.raises(UnsupportedTextualConstructError, match="bogus"):
        parse_epidoc_file(unknown_attribute, source_revision="deadbeef")


def test_edition_level_lb_between_explicit_textparts_starts_following_part(
    tmp_path: Path,
) -> None:
    path = _write(
        tmp_path,
        "parts-lb.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="parts-lb"><text><body>
        <div type="edition" subtype="transcription" xml:id="parts-lb.transcription">
          <div type="textpart" n="a"><p>Alpha</p></div>
          <lb/>
          <div type="textpart" n="b"><p>Beta</p></div>
        </div>
        </body></text></TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")

    parts = _nodes(ir, NodeType.TEXTPART)
    assert len(parts) == 2
    second = next(node for node in parts if node.feature("source_n") == "b")
    boundary = next(sign for sign in ir.signs if sign.synthetic_kind == "line_break")
    assert boundary.key in second.sign_keys

    line_break = next(
        node
        for node in _nodes(ir, NodeType.MARKUP)
        if node.feature("kind") == "line_break"
    )
    edition = next(node for node in _nodes(ir, NodeType.EDITION))
    assert IREdge(EdgeType.PARENT, line_break.key, edition.key) in ir.edges
