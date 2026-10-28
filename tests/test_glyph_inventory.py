"""#108 RED: exact parser-condition source census ahead of Unicode glyph mapping."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iip_tf.glyph_inventory import GlyphInventoryError, audit_glyph_sources, scan_glyph_xml
from iip_tf.source_repair import PINNED_IIP_REVISION


def _xml(path: Path, text: str) -> Path:
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<text><body>' + text + '</body></text></TEI>', encoding="utf-8"
    )
    return path


def test_empty_glyphs_separate_real_refs_from_filled_and_unreferenced(tmp_path: Path) -> None:
    path = _xml(tmp_path / "masa0286.xml", (
        '<div type="edition" subtype="transcription"><p>'
        '<g ref="phoen-gaml"/><g ref="phoen-delt"></g>'
        '<g ref="cross">+</g><g ref="foo"><hi>F</hi></g>'
        '<g ref="bird">   </g><g/><g type="char"/>'
        '</p></div>'
    ))
    result = scan_glyph_xml(path)
    assert result["record"] == "masa0286"
    assert result["empty_referenced"] == 3
    assert result["empty_unreferenced"] == 2
    assert result["filled_referenced"] == 2
    assert result["refs"] == {"bird": 1, "phoen-delt": 1, "phoen-gaml": 1}
    assert result["layers"] == {"transcription": 3}


def test_segmented_and_diplomatic_are_counted_not_normalized(tmp_path: Path) -> None:
    a = _xml(tmp_path / "a.xml", (
        '<div type="edition" subtype="diplomatic">'
        '<g ref="cross"/><g ref="cross"/></div>'
        '<div type="edition" subtype="transcription_segmented">'
        '<g ref="cross"/><g/></div>'
    ))
    b = _xml(tmp_path / "b.xml", (
        '<div type="edition" subtype="transcription"><g ref="cross"/></div>'
    ))
    report = audit_glyph_sources((a, b))
    assert report["source_records"] == 2
    assert report["records_with_empty_references"] == 2
    assert report["empty_referenced"] == 4
    assert report["empty_unreferenced"] == 1
    assert report["filled_referenced"] == 0
    assert report["refs"] == {"cross": 4}
    assert report["layers"] == {
        "diplomatic": 2,
        "transcription": 1,
        "transcription_segmented": 1,
    }
    assert report["by_record"] == {"a": 3, "b": 1}
    assert json.loads(json.dumps(report, sort_keys=True)) == report


def test_absent_layer_explicit_and_attribute_ref_xml_decoded(tmp_path: Path) -> None:
    p = _xml(
        tmp_path / "x.xml",
        '<g ref="ivy &amp; leaf"/><div><g ref="ivY-leaf"/></div>'
    )
    assert scan_glyph_xml(p)["refs"] == {"ivY-leaf": 1, "ivy & leaf": 1}
    assert scan_glyph_xml(p)["layers"] == {"unclassified": 2}


def test_malformed_input_and_duplicate_record_ids_fail_closed(tmp_path: Path) -> None:
    a = _xml(tmp_path / "a.xml", "<g ref='x'/>")
    with pytest.raises(GlyphInventoryError, match="duplicate"):
        audit_glyph_sources((a, a))
    bad = tmp_path / "invalid.xml"
    bad.write_text("<TEI><g></TEI>", encoding="utf-8")
    with pytest.raises(GlyphInventoryError, match="XML"):
        scan_glyph_xml(bad)
    with pytest.raises(GlyphInventoryError, match="no source"):
        audit_glyph_sources(())


def test_output_never_invents_unicode_or_source_glyphs(tmp_path: Path) -> None:
    source = _xml(tmp_path / "x.xml", (
        '<div type="edition" subtype="transcription">'
        '<g ref="phoen-gaml"/><g ref="phoen-???"/><g ref="cross">+</g></div>'
    ))
    report = audit_glyph_sources((source,))
    assert report["refs"] == {"phoen-???": 1, "phoen-gaml": 1}
    assert "𐤂" not in json.dumps(report)
    assert "((" not in json.dumps(report)

def test_pinned_bqut_conflict_uses_reviewed_source_repair_only(tmp_path: Path) -> None:
    """Actual bqut0002.xml conflict block is a known pin-specific source repair."""
    source = _xml(
        tmp_path / "bqut0002.xml",
        '<div type="edition" subtype="transcription">'
        '<g ref="phoen-gaml"/>'
        '</div>\n'
        '<<<<<<< Updated upstream\n'
        '=======\n'
        '\n'
        '>>>>>>> Stashed changes',
    )
    with pytest.raises(GlyphInventoryError, match="XML|conflict"):
        scan_glyph_xml(source)
    repaired = scan_glyph_xml(source, source_revision=PINNED_IIP_REVISION)
    assert repaired["refs"] == {"phoen-gaml": 1}
    assert repaired["empty_referenced"] == 1
    with pytest.raises(GlyphInventoryError, match="conflict|pinned"):
        scan_glyph_xml(source, source_revision="not-brown-pin")


def test_unreviewed_source_conflict_never_silently_recovers(tmp_path: Path) -> None:
    source = _xml(
        tmp_path / "unknown0001.xml",
        '<div><g ref="x"/></div>\n'
        '<<<<<<< Updated upstream\n'
        '=======\n'
        '\n'
        '>>>>>>> Stashed changes',
    )
    with pytest.raises(GlyphInventoryError, match="conflict"):
        scan_glyph_xml(source, source_revision=PINNED_IIP_REVISION)
