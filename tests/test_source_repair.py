from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from iip_tf.source_repair import (
    PINNED_IIP_REVISION,
    REPAIR_ID,
    SourceConflictError,
    repair_source_file,
    validate_source_directory,
)

FIXTURES = Path(__file__).parent / "fixtures" / "source_conflicts"

KNOWN_FILES = (
    "bqut0002.xml",
    "caes0433.xml",
    "sepp0018.xml",
    "sepp0019.xml",
    "sepp0020.xml",
    "sepp0021.xml",
    "sepp0024.xml",
)


@pytest.mark.parametrize("filename", KNOWN_FILES)
def test_known_pinned_conflicts_are_repaired_to_well_formed_xml(filename: str) -> None:
    result = repair_source_file(
        FIXTURES / filename,
        source_revision=PINNED_IIP_REVISION,
    )

    assert result.repaired is True
    assert result.repair_id == REPAIR_ID
    assert result.filename == filename
    assert result.source_revision == PINNED_IIP_REVISION
    assert result.conflict_count == 1
    assert "<<<<<<<" not in result.text
    assert "=======" not in result.text
    assert ">>>>>>>" not in result.text
    ET.fromstring(result.text)


def test_sepp0018_union_preserves_credit_without_duplicate_main_image() -> None:
    result = repair_source_file(
        FIXTURES / "sepp0018.xml",
        source_revision=PINNED_IIP_REVISION,
    )

    assert "<desc>Zev Radovan</desc>" in result.text
    assert result.text.count('graphic url="sepp0018.jpg"') == 1
    assert "images/thumbnails/i_sepp0018_t.jpg" in result.text


def test_sepp0024_union_preserves_thumbnail_comment_and_added_credit() -> None:
    result = repair_source_file(
        FIXTURES / "sepp0024.xml",
        source_revision=PINNED_IIP_REVISION,
    )

    assert "images/thumbnails/i_sepp0024_t.jpg" in result.text
    assert "<desc>Zev Radovan</desc>" in result.text


def test_caes0433_preserves_stashed_empty_description_without_inventing_text() -> None:
    result = repair_source_file(
        FIXTURES / "caes0433.xml",
        source_revision=PINNED_IIP_REVISION,
    )

    assert "<desc/>" in result.text
    assert "<desc>" not in result.text


def test_unknown_conflicted_file_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "unknown.xml"
    path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"><facsimile>
<<<<<<< Updated upstream
<graphic url="a.jpg"/>
=======
<graphic url="b.jpg"/>
>>>>>>> Stashed changes
</facsimile></TEI>""",
        encoding="utf-8",
    )

    with pytest.raises(SourceConflictError, match="unknown.xml"):
        repair_source_file(path, source_revision=PINNED_IIP_REVISION)


def test_changed_known_conflict_shape_fails_closed(tmp_path: Path) -> None:
    source = (FIXTURES / "sepp0024.xml").read_text(encoding="utf-8")
    source = source.replace(
        '<desc>Zev Radovan</desc>',
        '<desc>Different credit</desc>',
    )
    path = tmp_path / "sepp0024.xml"
    path.write_text(source, encoding="utf-8")

    with pytest.raises(SourceConflictError, match="researched conflict block"):
        repair_source_file(path, source_revision=PINNED_IIP_REVISION)


def test_conflicted_file_on_future_revision_is_not_repaired(tmp_path: Path) -> None:
    path = tmp_path / "sepp0021.xml"
    path.write_text(
        (FIXTURES / "sepp0021.xml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SourceConflictError, match="pinned IIP revision"):
        repair_source_file(path, source_revision="future-revision")


def test_well_formed_future_revision_passes_through_unchanged(tmp_path: Path) -> None:
    text = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body/></text></TEI>'
    path = tmp_path / "sepp0021.xml"
    path.write_text(text, encoding="utf-8")

    result = repair_source_file(path, source_revision="future-revision")

    assert result.repaired is False
    assert result.repair_id is None
    assert result.conflict_count == 0
    assert result.text == text


def test_directory_validation_accounts_clean_and_repaired_files(tmp_path: Path) -> None:
    (tmp_path / "bqut0002.xml").write_text(
        (FIXTURES / "bqut0002.xml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "clean.xml").write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body/></text></TEI>',
        encoding="utf-8",
    )

    report = validate_source_directory(
        tmp_path,
        source_revision=PINNED_IIP_REVISION,
    )

    assert report.total_xml == 2
    assert report.well_formed == 2
    assert report.repaired == 1
    assert report.repaired_files == ("bqut0002.xml",)
    assert report.failures == ()


def test_well_formed_future_revision_allows_marker_like_text(tmp_path: Path) -> None:
    text = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<p>Editorial separator: =======</p>'
        '</body></text></TEI>'
    )
    path = tmp_path / "future.xml"
    path.write_text(text, encoding="utf-8")

    result = repair_source_file(path, source_revision="future-revision")

    assert result.repaired is False
    assert result.text == text
