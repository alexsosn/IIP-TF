"""Source-attested IIP person register and native entity→person IR projection.

This is an *annotation from a separate Brown source*, not a name matcher or
prosopography. Unknown and contributor references stay unresolved.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import TypedDict

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode, NodeType

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
PINNED_PERSONS_BLOB = "bce14d6d33ddfa06b4b6d1a4ccbf43e19390ac62"


class PersonLinkAudit(TypedDict):
    resolved_entities: int
    distinct_people: int
    unresolved_targets: dict[str, int]


class PersonRegisterError(ValueError):
    """The person authority file cannot be interpreted without ambiguity."""


@dataclass(frozen=True)
class PersonRecord:
    person_id: str
    names: tuple[str, ...]
    sex: str | None
    faith: str | None


def git_blob_sha1(path: Path) -> str:
    """Authenticate original source bytes in Git's blob-object domain."""
    content = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_person_register(
    path: Path, *, expected_git_sha1: str | None = None,
) -> Mapping[str, PersonRecord]:
    """Read direct person entries, with no fuzzy ID or faith normalization."""
    try:
        if path.is_symlink() or not path.is_file():
            raise PersonRegisterError(f"missing or symlink person register: {path}")
        if expected_git_sha1 is not None:
            actual = git_blob_sha1(path)
            if actual != expected_git_sha1:
                raise PersonRegisterError(
                    f"person register Git blob mismatch: {actual} != {expected_git_sha1}"
                )
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise PersonRegisterError(f"cannot parse person register {path.name}") from error
    if _local(root.tag) != "listPerson":
        raise PersonRegisterError("person register root must be listPerson")
    entries: dict[str, PersonRecord] = {}
    for element in root:
        if _local(element.tag) != "person":
            raise PersonRegisterError(f"unexpected register element {_local(element.tag)}")
        pid = element.attrib.get(XML_ID)
        if not pid or pid in entries or "#" in pid or "/" in pid:
            raise PersonRegisterError(f"missing/duplicate/unsafe person xml:id: {pid!r}")
        sex = element.attrib.get("sex")
        if sex not in {None, "1", "2"}:
            raise PersonRegisterError(f"{pid}: unexpected source sex code {sex!r}")
        names = tuple(
            "".join(child.itertext()).strip()
            for child in element if _local(child.tag) == "persName"
        )
        if not names or any(not name for name in names):
            raise PersonRegisterError(f"{pid}: absent or blank persName")
        faiths = tuple(
            "".join(child.itertext()).strip()
            for child in element if _local(child.tag) == "faith"
        )
        if len(faiths) > 1:
            raise PersonRegisterError(f"{pid}: ambiguous multiple faith entries")
        faith = faiths[0] if faiths and faiths[0] else None
        entries[pid] = PersonRecord(pid, names, sex, faith)
    return MappingProxyType(entries)


def attach_person_register(
    ir: InscriptionIR, register: Mapping[str, PersonRecord],
) -> tuple[InscriptionIR, PersonLinkAudit]:
    """Link real name entities within their *own* inscription; never invent people."""
    if ir.nodes_of_type(NodeType.PERSON):
        raise PersonRegisterError("person register already attached")
    by_target: dict[str, list[IRNode]] = {}
    unresolved: Counter[str] = Counter()
    for entity in ir.nodes_of_type(NodeType.ENTITY):
        if entity.feature("entity_kind") != "person":
            continue
        ref = entity.feature("ref")
        if not isinstance(ref, str) or not ref.startswith("persons.xml#"):
            continue
        target = ref.partition("#")[2]
        if (
            not target or target not in register
            or not target.startswith(ir.identity.inscription_id + "p")
            or not entity.sign_keys
        ):
            unresolved[ref] += 1
            continue
        by_target.setdefault(target, []).append(entity)

    persons: list[IRNode] = []
    edges: list[IREdge] = []
    for pid, entities in sorted(by_target.items()):
        entry = register[pid]
        key = f"{ir.identity.inscription_id}#person:{pid}"
        # Preserve inscription sign order; person referents are *not* new text.
        wanted = {sign for entity in entities for sign in entity.sign_keys}
        keys = tuple(sign.key for sign in ir.signs if sign.key in wanted)
        if len(keys) != len(wanted):
            raise PersonRegisterError(f"{pid}: unresolved person-name sign span")
        features: list[tuple[str, str]] = [
            ("person_id", pid),
            ("person_name", entry.names[0]),
        ]
        if entry.sex is not None:
            features.append(("sex", entry.sex))
        if entry.faith is not None:
            features.append(("faith", entry.faith))
        if len(entry.names) > 1:
            features.append(("person_name_variants", " | ".join(entry.names[1:])))
        persons.append(IRNode(key, NodeType.PERSON, keys, tuple(features)))
        edges.extend(IREdge(EdgeType.PERSON_REF, entity.key, key) for entity in entities)
    return replace(
        ir, nodes=ir.nodes + tuple(persons), edges=ir.edges + tuple(edges)
    ), {
        "resolved_entities": len(edges),
        "distinct_people": len(persons),
        "unresolved_targets": dict(sorted(unresolved.items())),
    }
