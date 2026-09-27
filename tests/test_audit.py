from __future__ import annotations

import json
from pathlib import Path

from iip_tf.audit import audit_directory, render_markdown


def _write(path: Path, name: str, text: str) -> None:
    (path / name).write_text(text, encoding="utf-8")


def test_audit_counts_textual_and_metadata_constructs(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "greek0001.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="greek0001">
  <teiHeader>
    <fileDesc>
      <publicationStmt>
        <authority>Brown University</authority>
        <availability status="free"><licence>
          Creative Commons Attribution-NonCommercial 4.0 International License.
          <ref target="http://creativecommons.org/licenses/by-nc/4.0/"/>
          <ref>https://doi.org/10.26300/pz1d-st89</ref>
        </licence></availability>
      </publicationStmt>
      <sourceDesc><msDesc>
        <msContents><textLang mainLang="grc"/><msItem class="funerary" ana="jewish"/></msContents>
        <physDesc><handDesc><handNote ana="engraved"/><handNote ana="painted"/></handDesc></physDesc>
      </msDesc></sourceDesc>
    </fileDesc>
  </teiHeader>
  <facsimile><surface><graphic url="a.jpg"/></surface><surface><graphic url="b.jpg"/></surface></facsimile>
  <text><body>
    <div type="edition" subtype="transcription"><p>Α<unclear>Β</unclear><lb/>Γ<gap reason="lost" unit="character" quantity="2"/></p></div>
    <div type="edition" subtype="transcription_segmented"><p>
      <w xml:id="greek0001-1" xml:lang="grc">Α<unclear>Β</unclear></w>
      <w xml:id="greek0001-2" xml:lang="grc">Γ</w>
    </p></div>
    <div type="translation"><p>translation</p></div>
    <div type="commentary"><p>commentary</p></div>
  </body><back><div type="bibliography"><listBibl>
    <bibl xml:id="b1"><ptr target="IIP-001.xml"/></bibl>
    <bibl xml:id="b2"><ptr target="IIP-002.xml"/></bibl>
  </listBibl></div></back></text>
</TEI>""",
    )
    _write(
        tmp_path,
        "sem0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="sem0001">
  <teiHeader><fileDesc><sourceDesc><msDesc><msContents>
    <textLang mainLang="heb" otherLangs="arc"/>
  </msContents></msDesc></sourceDesc></fileDesc></teiHeader>
  <text><body>
    <div type="edition" subtype="transcription"><div type="textpart" n="a"><p xml:lang="heb">אב<lb/>גד</p></div></div>
  </body></text>
</TEI>""",
    )
    _write(
        tmp_path,
        "empty0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="empty0001">
  <teiHeader><fileDesc><sourceDesc><msDesc><msContents><textLang mainLang="arc"/></msContents></msDesc></sourceDesc></fileDesc></teiHeader>
  <text><body><div type="edition" subtype="transcription"><p/></div></body></text>
</TEI>""",
    )
    _write(tmp_path, "broken0001.xml", "<TEI><broken>")

    inventory = audit_directory(tmp_path, source_revision="deadbeef")

    assert inventory["schema_version"] == 1
    assert inventory["source"]["revision"] == "deadbeef"
    assert inventory["files"] == {
        "total_xml": 4,
        "parsed": 3,
        "malformed": 1,
        "test_or_non_inscription": 0,
    }
    assert inventory["transcriptions"]["records_with_transcription"] == 3
    assert inventory["transcriptions"]["records_with_segmented_transcription"] == 1
    assert inventory["transcriptions"]["records_with_unsegmented_only"] == 2
    assert inventory["transcriptions"]["empty_transcription_records"] == 1
    assert inventory["structure"]["records_with_textpart"] == 1
    assert inventory["structure"]["line_break_elements"] == 2
    assert inventory["languages"]["record_declarations"] == {"arc": 2, "grc": 1, "heb": 1}
    assert inventory["languages"]["token_declarations"] == {"grc": 2}
    assert inventory["metadata"]["max_bibliography_entries_per_record"] == 2
    assert inventory["metadata"]["max_hand_notes_per_record"] == 2
    assert inventory["metadata"]["max_facsimile_surfaces_per_record"] == 2
    assert inventory["licence"]["records_with_cc_by_nc_4_0"] == 1
    assert inventory["licence"]["records_with_iip_doi"] == 1
    assert inventory["elements"]["transcription"]["unclear"] == 1
    assert inventory["elements"]["transcription"]["gap"] == 1


def test_audit_output_is_deterministic_and_markdown_is_derived(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "x0001.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="x0001"><text><body>
        <div type="edition" subtype="transcription"><p>abc</p></div>
        </body></text></TEI>""",
    )

    first = audit_directory(tmp_path, source_revision="abc")
    second = audit_directory(tmp_path, source_revision="abc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    report = render_markdown(first)
    assert "# IIP corpus audit" in report
    assert "Source revision: `abc`" in report
    assert "Total XML files: **1**" in report
