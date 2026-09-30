from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode
from iip_tf.text_parser import parse_epidoc_file


def _write(path: Path, name: str, text: str) -> Path:
    target = path / name
    target.write_text(text, encoding="utf-8")
    return target


def _nodes(ir: InscriptionIR, node_type: str) -> list[IRNode]:
    return [node for node in ir.nodes if node.node_type.value == node_type]


def test_scalar_metadata_and_dimensions_are_preserved_without_overwriting(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "meta.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="meta">
  <teiHeader><fileDesc><publicationStmt><idno type="IIP">Meta 1</idno></publicationStmt>
  <sourceDesc><msDesc>
    <msContents>
      <textLang mainLang="la" otherLangs="grc arc"/>
      <msItem class="#dedicatory" ana="other_religion" cert="medium"><p>summary</p></msItem>
    </msContents>
    <physDesc>
      <objectDesc ana="#block">
        <supportDesc ana="limestone">
          <support>
            <p>support note</p>
            <dimensions type="surface" unit="cm">
              <height>64</height><width atLeast="100" atMost="102">102</width>
            </dimensions>
          </support>
          <condition ana="complete"><p>poorly preserved</p></condition>
        </supportDesc>
        <layoutDesc><layout columns="1" writtenLines="6"><p>layout note</p></layout></layoutDesc>
      </objectDesc>
      <handDesc>
        <handNote ana="#engraved">
          <dimensions type="letter" extent="height" unit="cm" atLeast="4.2" atMost="7.5"/>
          <p>serifed letters</p>
        </handNote>
      </handDesc>
    </physDesc>
    <history>
      <origin>
        <date period="period:roman" notBefore="-0020" notAfter="0070" precision="low">20 BCE to 70 CE</date>
        <placeName>
          <region cert="high">Judaea</region>
          <settlement ref="pleiades:1" cert="medium">Jerusalem<geo>31.7 35.2</geo></settlement>
          <geogName type="site">Kidron Valley</geogName>
          <geogFeat type="locus">Tomb 5</geogFeat>
        </placeName>
        <p>origin note</p>
      </origin>
      <provenance><placeName>Museum store</placeName></provenance>
    </history>
  </msDesc></sourceDesc></fileDesc></teiHeader>
  <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    inscription = _nodes(ir, "inscription")[0]

    assert inscription.feature("main_lang") == "la"
    assert inscription.feature("other_langs") == "grc arc"
    assert inscription.feature("genre") == "#dedicatory"
    assert inscription.feature("genre_cert") == "medium"
    assert inscription.feature("religion") == "other_religion"
    assert inscription.feature("object_type") == "#block"
    assert inscription.feature("material") == "limestone"
    assert inscription.feature("condition") == "complete"
    assert inscription.feature("condition_note") == "poorly preserved"
    assert inscription.feature("layout_columns") == "1"
    assert inscription.feature("layout_written_lines") == "6"
    assert inscription.feature("layout_note") == "layout note"
    assert inscription.feature("date_not_before") == "-0020"
    assert inscription.feature("date_not_before_int") == -20
    assert inscription.feature("date_not_after") == "0070"
    assert inscription.feature("date_not_after_int") == 70
    assert inscription.feature("date_text") == "20 BCE to 70 CE"
    assert inscription.feature("date_precision") == "low"
    assert inscription.feature("period_ref") == "period:roman"
    assert inscription.feature("region") == "Judaea"
    assert inscription.feature("region_cert") == "high"
    assert inscription.feature("settlement") == "Jerusalem"
    assert inscription.feature("settlement_cert") == "medium"
    assert inscription.feature("settlement_ref") == "pleiades:1"
    assert inscription.feature("site") == "Kidron Valley"
    assert inscription.feature("locus") == "Tomb 5"
    assert inscription.feature("geo") == "31.7 35.2"
    assert inscription.feature("origin_note") == "origin note"
    assert inscription.feature("provenance_place") == "Museum store"

    dimensions = _nodes(ir, "dimension")
    assert len(dimensions) == 2
    surface = next(node for node in dimensions if node.feature("dimension_type") == "surface")
    assert surface.feature("dimension_unit") == "cm"
    assert surface.feature("height") == "64"
    assert surface.feature("width") == "102"
    assert surface.feature("width_min") == "100"
    assert surface.feature("width_max") == "102"

    hand = _nodes(ir, "hand")[0]
    assert hand.feature("technique") == "#engraved"
    assert hand.feature("note") == "serifed letters"
    letter = next(node for node in dimensions if node.feature("dimension_type") == "letter")
    assert letter.feature("dimension_extent") == "height"
    assert letter.feature("at_least") == "4.2"
    assert letter.feature("at_most") == "7.5"
    assert any(
        edge.edge_type == EdgeType.PARENT
        and edge.source == letter.key
        and edge.target == hand.key
        for edge in ir.edges
    )


def test_bibliography_scopes_repeat_and_local_ana_resolves_to_cites(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "bibl.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="bibl">
  <text>
    <body>
      <div type="edition" subtype="transcription" ana="#b1"><p>A</p></div>
      <div type="translation" ana="#taxonomy #b2"><p>B</p></div>
    </body>
    <back><div type="bibliography"><listBibl>
      <bibl xml:id="b1">
        <ptr type="biblItem" target="IIP-001.xml"/>
        <biblScope unit="page">10</biblScope>
        <biblScope unit="page" n="fig">fig. 2</biblScope>
      </bibl>
      <bibl xml:id="b2"><ptr target="IIP-002.xml"/></bibl>
    </listBibl></div></back>
  </text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    bibls = _nodes(ir, "bibl")
    scopes = _nodes(ir, "bibl_scope")

    assert len(bibls) == 2
    assert len(scopes) == 2
    b1 = next(node for node in bibls if node.feature("source_id") == "b1")
    b2 = next(node for node in bibls if node.feature("source_id") == "b2")
    assert b1.feature("target") == "IIP-001.xml"
    assert b1.feature("ptr_type") == "biblItem"
    assert {scope.feature("scope") for scope in scopes} == {"10", "fig. 2"}
    assert {scope.feature("scope_n") for scope in scopes} == {None, "fig"}
    assert all(
        any(
            edge.edge_type == EdgeType.PARENT
            and edge.source == scope.key
            and edge.target == b1.key
            for edge in ir.edges
        )
        for scope in scopes
    )

    editions = _nodes(ir, "edition")
    transcription = next(
        node for node in editions if node.feature("edition_kind") == "transcription"
    )
    translation = next(
        node for node in editions if node.feature("edition_kind") == "translation"
    )
    cites = {(edge.source, edge.target) for edge in ir.edges if edge.edge_type == EdgeType.CITES}
    assert (transcription.key, b1.key) in cites
    assert (translation.key, b2.key) in cites
    assert all("taxonomy" not in target for _, target in cites)


def test_facsimile_surface_images_keep_explicit_credit_without_guessing_plain_desc(
    tmp_path: Path,
) -> None:
    path = _write(
        tmp_path,
        "facsimile.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="facsimile">
  <facsimile>
    <graphic url="direct.jpg"/>
    <surface>
      <desc>Front. <persName role="Credit">Zev Radovan</persName></desc>
      <graphic url="front.jpg"/>
      <graphic url="detail.jpg"/>
      <note>commons.example/front</note>
    </surface>
    <surface>
      <desc>Gary Todd - Flickr (public domain)</desc>
      <graphic url="plain.jpg"/>
    </surface>
  </facsimile>
  <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    surfaces = _nodes(ir, "facsimile_surface")
    images = _nodes(ir, "image")

    assert len(surfaces) == 2
    assert len(images) == 4
    credited_surface = next(
        node for node in surfaces if node.feature("description") == "Front. Zev Radovan"
    )
    assert credited_surface.feature("note") == "commons.example/front"

    credited = [node for node in images if node.feature("url") in {"front.jpg", "detail.jpg"}]
    assert {node.feature("credit") for node in credited} == {"Zev Radovan"}
    assert {node.feature("credit_role") for node in credited} == {"Credit"}

    plain = next(node for node in images if node.feature("url") == "plain.jpg")
    assert plain.feature("credit") is None
    assert plain.feature("description") == "Gary Todd - Flickr (public domain)"

    direct = next(node for node in images if node.feature("url") == "direct.jpg")
    inscription = _nodes(ir, "inscription")[0]
    assert any(
        edge.edge_type == EdgeType.PARENT
        and edge.source == direct.key
        and edge.target == inscription.key
        for edge in ir.edges
    )


def test_decorations_and_revisions_remain_repeatable_nodes(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "repeat.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="repeat">
  <teiHeader><fileDesc><sourceDesc><msDesc><physDesc>
    <decoDesc>
      <decoNote ana="#zigzag"><ab>zigzag bands</ab><locus>front</locus></decoNote>
      <decoNote ana="#rosette"><ab>rosette</ab><locus>side</locus></decoNote>
    </decoDesc>
  </physDesc></msDesc></sourceDesc></fileDesc>
  <revisionDesc>
    <change when="2020-01-01" who="A">Creation</change>
    <change when-custom="later" who="B">Revision</change>
  </revisionDesc></teiHeader>
  <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
</TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    decorations = _nodes(ir, "decoration")
    revisions = _nodes(ir, "revision")

    assert len(decorations) == 2
    assert {
        (n.feature("type"), n.feature("description"), n.feature("decoration_locus"))
        for n in decorations
    } == {
        ("#zigzag", "zigzag bands", "front"),
        ("#rosette", "rosette", "side"),
    }
    assert len(revisions) == 2
    assert {
        (
            n.feature("when"),
            n.feature("when_custom"),
            n.feature("who"),
            n.feature("description"),
        )
        for n in revisions
    } == {
        ("2020-01-01", None, "A", "Creation"),
        (None, "later", "B", "Revision"),
    }


def test_metadata_scalar_cardinality_and_mapped_unknowns_fail_closed(tmp_path: Path) -> None:
    repeated = _write(
        tmp_path,
        "repeated.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><sourceDesc><msDesc>
          <msContents>
            <msItem class="#a"/><msItem class="#b"/>
          </msContents>
        </msDesc></sourceDesc></fileDesc></teiHeader>
        <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
        </TEI>""",
    )
    unknown = _write(
        tmp_path,
        "unknown.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><sourceDesc><msDesc>
          <physDesc><handDesc><handNote ana="#engraved" bogus="x"/></handDesc></physDesc>
        </msDesc></sourceDesc></fileDesc></teiHeader>
        <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
        </TEI>""",
    )

    with pytest.raises(ValueError, match="genre"):
        parse_epidoc_file(repeated, source_revision="deadbeef")

    with pytest.raises(ValueError, match="handNote@bogus"):
        parse_epidoc_file(unknown, source_revision="deadbeef")


def test_support_note_preserves_multiple_source_paragraphs_in_order(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "support-paragraphs.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><sourceDesc><msDesc>
          <physDesc><objectDesc><supportDesc><support>
            <p>First support paragraph.</p>
            <dimensions type="surface" unit="cm"><height>1</height></dimensions>
            <p>Second support paragraph.</p>
          </support></supportDesc></objectDesc></physDesc>
        </msDesc></sourceDesc></fileDesc></teiHeader>
        <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    inscription = _nodes(ir, "inscription")[0]

    assert inscription.feature("support_note") == (
        "First support paragraph.\n\nSecond support paragraph."
    )


def test_nested_facsimile_surfaces_preserve_parent_hierarchy(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "nested-surface.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <facsimile>
            <surface>
              <desc>Left side.</desc><graphic url="left.jpg"/>
              <surface><desc>Right side.</desc><graphic url="right.jpg"/></surface>
            </surface>
          </facsimile>
          <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    surfaces = _nodes(ir, "facsimile_surface")
    images = _nodes(ir, "image")

    assert len(surfaces) == 2
    outer = next(node for node in surfaces if node.feature("description") == "Left side.")
    inner = next(node for node in surfaces if node.feature("description") == "Right side.")
    right = next(node for node in images if node.feature("url") == "right.jpg")

    assert IREdge(EdgeType.PARENT, inner.key, outer.key) in ir.edges
    assert IREdge(EdgeType.PARENT, right.key, inner.key) in ir.edges


def test_unknown_child_inside_mapped_metadata_scope_fails_closed(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "unknown-child.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><sourceDesc><msDesc>
          <physDesc><handDesc><handNote ana="#engraved"><foo>lost structure</foo></handNote></handDesc></physDesc>
        </msDesc></sourceDesc></fileDesc></teiHeader>
        <text><body><div type="edition" subtype="transcription"><p>A</p></div></body></text>
        </TEI>""",
    )

    with pytest.raises(ValueError, match="handNote.*foo"):
        parse_epidoc_file(path, source_revision="deadbeef")
