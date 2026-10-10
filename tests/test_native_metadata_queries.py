"""Query native metadata after real EpiDoc -> IR -> Text-Fabric conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def test_research_metadata_queries_use_native_features_and_edges(tmp_path: Path) -> None:
    source = tmp_path / "query.xml"
    source.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="query">
        <teiHeader>
          <fileDesc><sourceDesc><msDesc>
            <msContents><textLang mainLang="grc"/></msContents>
            <physDesc>
              <objectDesc ana="#altar">
                <supportDesc ana="limestone">
                  <support>
                    <p>First support note.</p><p>Second support note.</p>
                    <dimensions type="surface" unit="cm">
                      <height>12</height><width>25</width>
                    </dimensions>
                  </support>
                </supportDesc>
              </objectDesc>
              <handDesc><handNote ana="#engraved">
                <dimensions type="letter" unit="cm" extent="height">
                  <height>1.4</height>
                </dimensions>
                <p>Lettering note.</p>
              </handNote></handDesc>
              <decoDesc><decoNote ana="#rosette"><ab>Rosette</ab></decoNote></decoDesc>
            </physDesc>
            <history><origin>
              <date period="period:roman" notBefore="-0010" notAfter="0020">
                10 BCE to 20 CE
              </date>
              <placeName>
                <region>Judaea</region>
                <settlement ref="pleiades:638">Jerusalem</settlement>
              </placeName>
            </origin></history>
          </msDesc></sourceDesc></fileDesc>
          <revisionDesc><change when="2020-01-01" who="Editor">Revision.</change></revisionDesc>
        </teiHeader>
        <facsimile><surface>
          <desc>Front <persName role="Credit">Photographer</persName></desc>
          <graphic url="front.jpg"/>
          <surface><desc>Detail</desc><graphic url="detail.jpg"/></surface>
        </surface></facsimile>
        <text>
          <body><div type="edition" subtype="transcription" ana="#b1">
            <p><persName ref="person:1">ADA</persName></p>
          </div></body>
          <back><div type="bibliography"><listBibl>
            <bibl xml:id="b1"><ptr target="reference.xml"/>
              <biblScope unit="page">12</biblScope>
              <biblScope unit="page">13</biblScope>
            </bibl>
          </listBibl></div></back>
        </text>
        </TEI>""",
        encoding="utf-8",
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    output = tmp_path / "tf"
    write_tf_corpus((ir,), output, converter_commit="fixture-commit")

    api: Any = Fabric(locations=str(output), silent=True).loadAll(silent=True)
    assert api
    F, E, L, S = api.F, api.E, api.L, api.S
    inscription = F.otype.s("inscription")[0]

    # Exact raw source values and derived numeric dates remain separate.
    assert F.date_not_before.v(inscription) == "-0010"
    assert F.date_not_before_int.v(inscription) == -10
    assert F.date_not_after.v(inscription) == "0020"
    assert F.date_not_after_int.v(inscription) == 20
    assert F.period_ref.v(inscription) == "period:roman"
    assert F.region.v(inscription) == "Judaea"
    assert F.settlement.v(inscription) == "Jerusalem"
    assert F.settlement_ref.v(inscription) == "pleiades:638"
    assert F.material.v(inscription) == "limestone"
    assert F.object_type.v(inscription) == "#altar"

    # Standard TF search operates on inscription features.
    hits = S.search("inscription region=Judaea")
    assert any(row[0] == inscription for row in hits)

    assert len(F.otype.s("support_note")) == 2
    notes = {F.note.v(n) for n in F.otype.s("support_note")}
    assert notes == {"First support note.", "Second support note."}
    assert all(inscription in E.parent.f(n) for n in F.otype.s("support_note"))

    hand = F.otype.s("hand")[0]
    letter = next(n for n in F.otype.s("dimension") if F.dimension_type.v(n) == "letter")
    surface_dimension = next(
        n for n in F.otype.s("dimension") if F.dimension_type.v(n) == "surface"
    )
    assert F.technique.v(hand) == "#engraved"
    assert F.height.v(surface_dimension) == "12"
    assert F.width.v(surface_dimension) == "25"
    assert F.height.v(letter) == "1.4"
    assert hand in E.parent.f(letter)

    assert F.type.v(F.otype.s("decoration")[0]) == "#rosette"
    assert F.when.v(F.otype.s("revision")[0]) == "2020-01-01"

    bibl = F.otype.s("bibl")[0]
    assert F.target.v(bibl) == "reference.xml"
    scopes = F.otype.s("bibl_scope")
    assert len(scopes) == 2
    assert {F.scope.v(n) for n in scopes} == {"12", "13"}
    assert all(bibl in E.parent.f(n) for n in scopes)
    edition = F.otype.s("edition")[0]
    assert bibl in E.cites.f(edition)

    surfaces = F.otype.s("facsimile_surface")
    assert len(surfaces) == 2
    outer = next(n for n in surfaces if F.description.v(n) == "Front Photographer")
    inner = next(n for n in surfaces if F.description.v(n) == "Detail")
    assert outer in E.parent.f(inner)
    images = F.otype.s("image")
    assert len(images) == 2
    front = next(n for n in images if F.url.v(n) == "front.jpg")
    detail = next(n for n in images if F.url.v(n) == "detail.jpg")
    assert outer in E.parent.f(front)
    assert inner in E.parent.f(detail)
    assert F.credit.v(front) == "Photographer"

    person = F.otype.s("entity")[0]
    assert F.entity_kind.v(person) == "person"
    assert F.ref.v(person) == "person:1"
    assert tuple(L.d(person, otype="sign"))
    assert inscription in L.u(person, otype="inscription")

    assert F.date_not_before.meta["sourceCommit"] == "fixture-revision"
    assert F.date_not_before.meta["license"] == "CC BY-NC 4.0"
