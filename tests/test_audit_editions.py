from __future__ import annotations

from pathlib import Path

from iip_tf.audit import audit_directory, render_markdown


def _write(path: Path, name: str, text: str) -> None:
    (path / name).write_text(text, encoding="utf-8")


def test_audit_separates_diplomatic_edition_surface(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "a.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="a">
  <text><body>
    <div type="edition" subtype="diplomatic" xml:id="a.diplomatic"
         corresp="#a.transcription" ana="#b1" xml:lang="grc">
      <p><g ref="cross">+</g>Α<gap reason="lost" unit="character" quantity="1"/>
      <lb/><div type="textpart" subtype="reverse"><p>Β</p></div></p>
    </div>
    <div type="edition" subtype="transcription" xml:id="a.transcription">
      <p>Α<supplied reason="lost">Β</supplied></p>
    </div>
    <div type="edition" subtype="transcription_segmented">
      <p><w xml:id="a-1" xml:lang="grc">ΑΒ</w></p>
    </div>
  </body></text>
</TEI>""",
    )
    _write(
        tmp_path,
        "b.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="b">
  <text><body>
    <div type="edition" subtype="diplomatic"><p/></div>
  </body></text>
</TEI>""",
    )

    inventory = audit_directory(tmp_path, source_revision="abc")

    diplomatic = inventory["editions"]["by_subtype"]["diplomatic"]
    assert diplomatic == {
        "divs": 2,
        "records": 2,
        "nonempty_divs": 1,
        "records_with_nonempty": 1,
        "line_break_elements": 1,
        "textpart_divs": 1,
        "with_xml_id": 1,
        "with_corresp": 1,
        "with_ana": 1,
        "with_xml_lang": 1,
    }
    assert inventory["editions"]["by_subtype"]["transcription"]["records"] == 1
    assert inventory["editions"]["by_subtype"]["transcription_segmented"]["records"] == 1
    assert inventory["elements"]["diplomatic"]["g"] == 1
    assert inventory["elements"]["diplomatic"]["gap"] == 1

    report = render_markdown(inventory)
    assert "## Edition layers" in report
    assert "| `diplomatic` | 2 | 2 | 1 | 1 | 1 | 1 |" in report
    assert "### diplomatic" in report
    assert "| `gap` | 1 |" in report


def test_audit_reports_every_observed_edition_subtype(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "x.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="x">
  <text><body>
    <div type="edition" subtype="source_facsimile"><p>Χ</p></div>
  </body></text>
</TEI>""",
    )

    inventory = audit_directory(tmp_path, source_revision="abc")

    assert inventory["editions"]["by_subtype"]["source_facsimile"]["divs"] == 1
    assert inventory["editions"]["by_subtype"]["source_facsimile"]["nonempty_divs"] == 1


def test_audit_classifies_multi_target_corresp_relations(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "relations.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="relations">
  <text><body>
    <div type="edition" subtype="diplomatic"
         corresp="#relations.transcription #relations.translation #external"/>
    <div type="edition" subtype="transcription"
         corresp="#relations.diplomatic"/>
    <div type="edition" subtype="source_facsimile"
         corresp="#relations.transcription_segmented"/>
  </body></text>
</TEI>""",
    )

    inventory = audit_directory(tmp_path, source_revision="abc")

    assert inventory["editions"]["corresp_targets_by_subtype"]["diplomatic"] == {
        "other": 1,
        "transcription": 1,
        "translation": 1,
    }
    assert inventory["editions"]["corresp_targets_by_subtype"]["transcription"] == {
        "diplomatic": 1,
    }
    assert inventory["editions"]["corresp_targets_by_subtype"]["source_facsimile"] == {
        "transcription_segmented": 1,
    }

    report = render_markdown(inventory)
    assert "### Edition corresp target classes" in report
    assert "| `diplomatic` | `transcription` | 1 |" in report
    assert "| `diplomatic` | `translation` | 1 |" in report
    assert "| `diplomatic` | `other` | 1 |" in report


def test_audit_classifies_translation_source_corresp_relations(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "translation-relations.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="translation-relations">
  <text><body>
    <div type="translation"
         corresp="#translation-relations.diplomatic #translation-relations.transcription"/>
    <div type="edition" subtype="diplomatic"
         corresp="#translation-relations.translation"/>
  </body></text>
</TEI>""",
    )

    inventory = audit_directory(tmp_path, source_revision="abc")

    assert inventory["relations"]["corresp_targets_by_source_context"] == {
        "diplomatic": {"translation": 1},
        "translation": {"diplomatic": 1, "transcription": 1},
    }

    report = render_markdown(inventory)
    assert "### Corresp target classes by source context" in report
    assert "| `translation` | `diplomatic` | 1 |" in report
    assert "| `translation` | `transcription` | 1 |" in report
