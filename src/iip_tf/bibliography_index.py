"""Read only the source-attested IIP keys of Brown's TEI Zotero export.

One TEI biblStruct is one source work, even if multiple explicit IIP IDs
identify it. This module does not infer a citation target or create TF nodes.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from iip_tf.person_register import git_blob_sha1

_TEI = "http://www.tei-c.org/ns/1.0"
_XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_NS = {"tei": _TEI}
_IIP_KEY = re.compile(r"IIP-[0-9]+")


class BibliographyIndexError(ValueError):
    """An authority source key cannot be interpreted without ambiguity."""


@dataclass(frozen=True)
class BibliographyEntry:
    ordinal: int  # one-based TEI biblStruct position, including unkeyed works
    keys: tuple[str, ...]  # exact source identifiers (never guessed aliases)
    work_type: str | None
    analytic_title: str | None
    monograph_title: str | None


@dataclass(frozen=True)
class BibliographyIndex:
    entries: tuple[BibliographyEntry, ...]
    by_key: Mapping[str, BibliographyEntry]
    unkeyed_ordinals: tuple[int, ...]
    source_git_blob: str


def _source_key(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = value.strip()
    return parsed if _IIP_KEY.fullmatch(parsed) else None


def _source_title(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    parsed = " ".join("".join(node.itertext()).split())
    return parsed or None


def read_bibliography_index(
    path: Path, *, expected_git_sha1: str | None = None,
) -> BibliographyIndex:
    """Index literal IIP source keys from correctly nested TEI work entries.

    The same key assigned to two distinct works is an error. Distinct keys
    *on one work* remain separately searchable aliases of that source work.
    The absence of a key is reported, not filled by a guessed identifier.
    """
    if path.is_symlink():
        raise BibliographyIndexError(f"symlink bibliography authority: {path}")
    if not path.is_file():
        raise BibliographyIndexError(f"missing bibliography authority: {path}")
    try:
        # Authenticate and parse the *same* captured bytes. Two file reads
        # create a race where the checked XML differs from the indexed XML.
        source = path.read_bytes()
        header = b"blob " + str(len(source)).encode("ascii") + b"\\0"
        blob = hashlib.sha1(header + source, usedforsecurity=False).hexdigest()
        if expected_git_sha1 is not None and blob != expected_git_sha1:
            raise BibliographyIndexError(
                f"bibliography Git blob mismatch: {blob} != {expected_git_sha1}"
            )
        root = ET.fromstring(source)
    except (OSError, UnicodeError, ET.ParseError) as exc:
        raise BibliographyIndexError(f"cannot parse bibliography authority: {path}") from exc
    if root.tag != f"{{{_TEI}}}TEI":
        raise BibliographyIndexError("bibliography authority must be namespaced TEI")

    works = root.findall(
        "./tei:text/tei:body/tei:listBibl/tei:biblStruct", _NS
    )
    if not works or len(works) != len(root.findall(".//tei:biblStruct", _NS)):
        raise BibliographyIndexError(
            "unsupported or missing TEI text/body/listBibl/biblStruct structure"
        )

    entries: list[BibliographyEntry] = []
    indexed: dict[str, BibliographyEntry] = {}
    unkeyed: list[int] = []
    for ordinal, work in enumerate(works, start=1):
        keys: list[str] = []
        for call_number in work.findall(
            "./tei:monogr/tei:idno[@type='callNumber']", _NS
        ):
            value = _source_key(_source_title(call_number))
            if value is not None and value not in keys:
                keys.append(value)
        for tag in work.findall(
            "./tei:note[@type='tags']/tei:note[@type='tag']", _NS
        ):
            value = _source_key(tag.get(_XML_ID))
            if value is not None and value not in keys:
                keys.append(value)
        entry = BibliographyEntry(
            ordinal=ordinal,
            keys=tuple(keys),
            work_type=work.get("type"),
            analytic_title=_source_title(work.find("./tei:analytic/tei:title", _NS)),
            monograph_title=_source_title(work.find("./tei:monogr/tei:title", _NS)),
        )
        entries.append(entry)
        if not keys:
            unkeyed.append(ordinal)
        for key in keys:
            prior = indexed.get(key)
            if prior is not None:
                raise BibliographyIndexError(
                    f"duplicate bibliography key {key!r} on "
                    f"works {prior.ordinal} and {ordinal}"
                )
            indexed[key] = entry
    return BibliographyIndex(
        entries=tuple(entries),
        by_key=MappingProxyType(indexed),
        unkeyed_ordinals=tuple(unkeyed),
        source_git_blob=blob,
    )
