"""#62 RED-first: exact source-key authority index, no inferred bibliography links."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


def _reader() -> Any:
    return importlib.import_module("iip_tf.bibliography_index")


def _document(*entries: str) -> str:
    return (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
        '<text><body><listBibl>'
        + "".join(entries)
        + '</listBibl></body></text></TEI>'
    )


def _fixture(tmp_path: Path, xml: str | None = None) -> Path:
    path = tmp_path / "iip-zotero-export.xml"
    path.write_text(xml if xml is not None else _document(
        # Exact Brown structural example: key only in monogr/idno.
        '<biblStruct type="journalArticle"><analytic><title level="a"/></analytic>'
        '<monogr><title level="j">l’Année Épigraphique</title>'
        '<idno type="callNumber">IIP-380</idno></monogr></biblStruct>',
        # Non-IIP tag must not be treated as an IIP ID; source key is xml:id.
        '<biblStruct type="journalArticle"><analytic><title level="a">'
        'A Greek Ostracon from Masada</title></analytic><monogr>'
        '<title level="j">Israel Exploration Journal</title></monogr>'
        '<note type="tags"><note type="tag" xml:id="IEJ1995d">IEJ1995d</note>'
        '<note type="tag" xml:id="IIP-609">IIP-609</note></note></biblStruct>',
        # A genuine Brown publication carries TWO IIP IDs, not two works.
        '<biblStruct type="journalArticle"><analytic><title level="a">'
        'Tombeau et Ossuaires Juifs Récemment Découverts</title></analytic>'
        '<note type="tags"><note type="tag" xml:id="IIP-001">IIP-001</note>'
        '<note type="tag" xml:id="IIP-694">IIP-694</note></note></biblStruct>',
        '<!-- <biblStruct><note type="tags"><note type="tag" '
        'xml:id="IIP-777">Fake</note></note></biblStruct> -->',
        '<biblStruct type="book"><monogr><title level="m">No key</title>'
        '</monogr></biblStruct>',
        '<biblStruct type="book"><monogr><title level="m">ISBN only</title>'
        '<idno type="ISBN">IIP-999</idno></monogr></biblStruct>',
        '<biblStruct type="book"><monogr><title level="m">Exact key</title>'
        '<idno type="callNumber">IIP-119</idno></monogr></biblStruct>',
    ), encoding="utf-8")
    return path


def test_real_structural_key_sources_multiple_aliases_and_unkeyed(
    tmp_path: Path,
) -> None:
    index = _reader().read_bibliography_index(_fixture(tmp_path))
    assert len(index.entries) == 6
    assert set(index.by_key) == {"IIP-380", "IIP-609", "IIP-001", "IIP-694", "IIP-119"}
    assert index.unkeyed_ordinals == (4, 5)
    assert index.by_key["IIP-001"] is index.by_key["IIP-694"]
    assert index.by_key["IIP-001"].keys == ("IIP-001", "IIP-694")
    assert index.by_key["IIP-001"].ordinal == 3
    assert index.by_key["IIP-380"].analytic_title is None
    assert index.by_key["IIP-380"].monograph_title == "l’Année Épigraphique"
    assert index.by_key["IIP-609"].analytic_title == "A Greek Ostracon from Masada"
    assert index.by_key["IIP-609"].monograph_title == "Israel Exploration Journal"
    assert index.by_key.get("IIP-777") is None
    assert index.by_key.get("IIP-999") is None
    assert index.by_key.get("IEJ1995d") is None
    assert index.by_key.get("IIP-0119") is None
    assert index.by_key["IIP-119"].monograph_title == "Exact key"


def test_two_separate_works_cannot_claim_same_iip_key(tmp_path: Path) -> None:
    path = _fixture(tmp_path, _document(
        '<biblStruct><monogr><idno type="callNumber">IIP-119</idno></monogr>'
        '</biblStruct>',
        '<biblStruct><note type="tags"><note type="tag" xml:id="IIP-119">'
        'IIP-119</note></note></biblStruct>',
    ))
    with pytest.raises(_reader().BibliographyIndexError, match="duplicate"):
        _reader().read_bibliography_index(path)


def test_repeat_same_key_in_one_work_is_not_an_ambiguous_duplicate(
    tmp_path: Path,
) -> None:
    path = _fixture(tmp_path, _document(
        '<biblStruct><monogr><idno type="callNumber">IIP-037</idno></monogr>'
        '<note type="tags"><note type="tag" xml:id="IIP-037">'
        'IIP-037</note></note></biblStruct>',
    ))
    index = _reader().read_bibliography_index(path)
    assert len(index.entries) == 1
    assert index.entries[0].keys == ("IIP-037",)
    assert set(index.by_key) == {"IIP-037"}


@pytest.mark.parametrize("xml", [
    '<TEI><text><body><listBibl><biblStruct/></listBibl></body></text></TEI>',
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>'
    '<biblStruct/></div></body></text></TEI>',
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>',
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><listBibl/>'
    '</body></text></TEI>',
])
def test_unsupported_authority_envelope_fails_closed(
    tmp_path: Path, xml: str,
) -> None:
    with pytest.raises(_reader().BibliographyIndexError):
        _reader().read_bibliography_index(_fixture(tmp_path, xml))


def test_source_git_blob_authentication_and_symlinks(
    tmp_path: Path,
) -> None:
    module = _reader()
    original = _fixture(tmp_path)
    with pytest.raises(module.BibliographyIndexError, match="blob mismatch"):
        module.read_bibliography_index(original, expected_git_sha1="0" * 40)
    actual = module.git_blob_sha1(original)
    assert module.read_bibliography_index(
        original, expected_git_sha1=actual
    ).source_git_blob == actual
    alias = tmp_path / "linked.xml"
    alias.symlink_to(original)
    with pytest.raises(module.BibliographyIndexError, match="symlink"):
        module.read_bibliography_index(alias)


def test_authenticated_xml_is_parsed_from_same_bytes_as_git_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A source file can change between separate checksum and XML reads."""
    path = _fixture(tmp_path)
    original = path.read_bytes()
    module = _reader()
    expected = module.git_blob_sha1(path)
    real_read = Path.read_bytes

    def change_on_read(self: Path) -> bytes:
        data = real_read(self)
        if self == path:
            path.write_bytes(b"<broken>")
        return data

    monkeypatch.setattr(Path, "read_bytes", change_on_read)
    try:
        index = module.read_bibliography_index(path, expected_git_sha1=expected)
    finally:
        path.write_bytes(original)
    assert len(index.entries) == 6
    assert index.source_git_blob == expected
