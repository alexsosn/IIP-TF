"""RED-first exact citation target resolution, preserving source spelling."""

from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.bibliography_index import read_bibliography_index
from iip_tf.bibliography_resolution import resolve_bibliography_target


def _authority(tmp_path: Path):
    xml = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><listBibl>'
        '<biblStruct><monogr><title>Ossuaries</title>'
        '<idno type="callNumber">IIP-119</idno></monogr></biblStruct>'
        '<biblStruct><monogr><title>Alias work</title></monogr>'
        '<note type="tags"><note type="tag" xml:id="IIP-001">IIP-001</note>'
        '<note type="tag" xml:id="IIP-694">IIP-694</note></note></biblStruct>'
        '<biblStruct><monogr><title>Explicit padded key</title>'
        '<idno type="callNumber">IIP-0119</idno></monogr></biblStruct>'
        '</listBibl></body></text></TEI>'
    )
    path = tmp_path / "authority.xml"
    path.write_text(xml, encoding="utf-8")
    return read_bibliography_index(path)


@pytest.mark.parametrize("target,key", [
    ("IIP-119.xml", "IIP-119"),
    ("IIP-119", "IIP-119"),
    ("IIP-001.xml", "IIP-001"),
    ("IIP-694.xml", "IIP-694"),
    ("IIP-0119.xml", "IIP-0119"),
])
def test_exact_source_keys_resolve_without_rewriting(
    tmp_path: Path, target: str, key: str,
) -> None:
    index = _authority(tmp_path)
    result = resolve_bibliography_target(index, target)
    assert result.target == target
    assert result.key == key
    assert result.entry is index.by_key[key]
    assert result.reason is None


def test_two_explicit_aliases_share_one_work(tmp_path: Path) -> None:
    index = _authority(tmp_path)
    left = resolve_bibliography_target(index, "IIP-001.xml")
    right = resolve_bibliography_target(index, "IIP-694")
    assert left.entry is right.entry
    assert left.entry is index.entries[1]


@pytest.mark.parametrize("target,reason", [
    (None, "missing"),
    ("", "missing"),
    ("IIP-120.xml", "unknown_key"),
    ("IIP-0118.xml", "unknown_key"),
    ("IIIP-119.xml", "malformed"),
    ("IIP-119.XML", "malformed"),
    ("IIP-119.xml#x", "malformed"),
    ("./IIP-119.xml", "malformed"),
    ("https://example.org/IIP-119.xml", "malformed"),
    (" IIP-119.xml", "malformed"),
    ("IIP-119.xml ", "malformed"),
    ("iip-119.xml", "malformed"),
    ("IIP-119.xml?download=1", "malformed"),
    ("IIP-119.xml/IIP-001", "malformed"),
    ("IIP-119a.xml", "malformed"),
    ("SEG", "malformed"),
    ("IIP.xml-", "malformed"),
])
def test_unresolved_never_fuzzily_resolves(
    tmp_path: Path, target: str | None, reason: str,
) -> None:
    result = resolve_bibliography_target(_authority(tmp_path), target)
    assert result.target == target
    assert result.key is None
    assert result.entry is None
    assert result.reason == reason


def test_pointer_type_is_not_a_precondition(tmp_path: Path) -> None:
    # The existing metadata parser records optional ptr_type separately.
    # This function resolves the raw target regardless of ptr_type.
    index = _authority(tmp_path)
    assert resolve_bibliography_target(index, "IIP-119.xml").entry is index.entries[0]
