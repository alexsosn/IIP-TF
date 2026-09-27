from __future__ import annotations

from pathlib import Path

from iip_tf.audit import audit_directory, render_markdown


def _write(path: Path, name: str, text: str) -> None:
    (path / name).write_text(text, encoding="utf-8")


def test_audit_classifies_primary_layer_overlap_and_edge_cases(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "normal.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="normal"><text><body>
  <div type="edition" subtype="transcription"><p>Α</p></div>
  <div type="edition" subtype="transcription_segmented"><p><w xml:id="n-1">Α</w></p></div>
  <div type="edition" subtype="diplomatic"><p>Α</p></div>
</body></text></TEI>""",
    )
    _write(
        tmp_path,
        "seg-only.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="seg-only"><text><body>
  <div type="edition" subtype="transcription_segmented"><p><w xml:id="s-1">Β</w></p></div>
</body></text></TEI>""",
    )
    _write(
        tmp_path,
        "empty-trans-diplomatic.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="empty-trans-diplomatic"><text><body>
  <div type="edition" subtype="transcription"><p/></div>
  <div type="edition" subtype="diplomatic"><p>Γ</p></div>
</body></text></TEI>""",
    )
    _write(
        tmp_path,
        "empty-trans-segmented.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="empty-trans-segmented"><text><body>
  <div type="edition" subtype="transcription"><p/></div>
  <div type="edition" subtype="transcription_segmented"><p><w xml:id="e-1">Δ</w></p></div>
</body></text></TEI>""",
    )
    _write(
        tmp_path,
        "none.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="none"><text><body>
  <div type="edition" subtype="transcription"><p/></div>
  <div type="edition" subtype="diplomatic"><p/></div>
</body></text></TEI>""",
    )
    _write(
        tmp_path,
        "multiple.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="multiple"><text><body>
  <div type="edition" subtype="transcription"><p>Ε</p></div>
  <div type="edition" subtype="transcription"><p>Ζ</p></div>
  <div type="edition" subtype="diplomatic"><p>ΕΖ</p></div>
  <div type="edition" subtype="diplomatic"><p>Η</p></div>
</body></text></TEI>""",
    )
    _write(tmp_path, "broken.xml", "<TEI><broken>")

    inventory = audit_directory(tmp_path, source_revision="abc")
    primary = inventory["primary_layer_candidates"]

    assert primary["cross_tab"] == {
        "transcription=absent|transcription_segmented=nonempty|diplomatic=absent": 1,
        "transcription=empty|transcription_segmented=absent|diplomatic=empty": 1,
        "transcription=empty|transcription_segmented=absent|diplomatic=nonempty": 1,
        "transcription=empty|transcription_segmented=nonempty|diplomatic=absent": 1,
        "transcription=nonempty|transcription_segmented=absent|diplomatic=nonempty": 1,
        "transcription=nonempty|transcription_segmented=nonempty|diplomatic=nonempty": 1,
    }
    assert primary["cases"]["transcription_absent_segmented_nonempty"] == ["seg-only.xml"]
    assert primary["cases"]["transcription_absent_or_empty_diplomatic_nonempty"] == [
        "empty-trans-diplomatic.xml"
    ]
    assert primary["cases"]["transcription_empty_segmented_nonempty"] == [
        "empty-trans-segmented.xml"
    ]
    assert primary["cases"]["no_nonempty_source_text_edition"] == ["none.xml"]
    assert primary["cases"]["multiple_transcription_divs"] == ["multiple.xml"]
    assert primary["cases"]["multiple_segmented_divs"] == []
    assert primary["cases"]["multiple_diplomatic_divs"] == ["multiple.xml"]

    report = render_markdown(inventory)
    assert "## Primary source-text layer overlap" in report
    assert "`seg-only.xml`" in report
    assert "`none.xml`" in report


def test_primary_layer_states_treat_editorial_empty_positions_as_nonempty(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "gap.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="gap"><text><body>
  <div type="edition" subtype="transcription">
    <p><gap reason="lost" extent="unknown" unit="character"/></p>
  </div>
</body></text></TEI>""",
    )

    inventory = audit_directory(tmp_path, source_revision="abc")

    assert inventory["primary_layer_candidates"]["cross_tab"] == {
        "transcription=nonempty|transcription_segmented=absent|diplomatic=absent": 1
    }
    assert inventory["primary_layer_candidates"]["cases"]["no_nonempty_source_text_edition"] == []
