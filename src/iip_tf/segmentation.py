"""Resolve duplicate IIP word-segmentation layers without guessing precedence."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

PINNED_IIP_REVISION = "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NS}}}id"
XML_LANG = f"{{{XML_NS}}}lang"
TOKEN_TAGS = {"w", "num", "orig"}

_ZOOR0453_CHANGES = ("c2021-06-16", "c2022-03-29")
_ZOOR0453_IDS = tuple(f"zoor0453-{index}" for index in range(1, 14))
_ZOOR0453_KINDS = ("w",) * 12 + ("orig",)
_ZOOR0453_TEXT = (
    "תתניח",
    "נפשה",
    "דחנינה",
    "כהנה",
    "בר",
    "יעקב",
    "דמית",
    "בעסרה",
    "יומין",
    "בירח",
    "טיבת",
    "שנת",
    "מ",
)


class SegmentationConflictError(ValueError):
    """Raised when duplicate segmented editions cannot be resolved from source evidence."""


@dataclass(frozen=True)
class SegmentationResolution:
    """Result of choosing the source layer that supplies token segmentation."""

    selected_index: int | None
    status: str
    suppressed_indices: tuple[int, ...]
    source_changes: tuple[str, ...]
    conflict_fields: tuple[str, ...]


def _local_name(name: str) -> str:
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def _normalise_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _meaningfully_nonempty(element: ET.Element) -> bool:
    if any(part.strip() for part in element.itertext()):
        return True
    for child in element.iter():
        if child is element:
            continue
        if _local_name(child.tag) not in {"div", "p", "lb", "pb", "cb"}:
            return True
    return False


def _tokens(div: ET.Element) -> tuple[ET.Element, ...]:
    tokens: list[ET.Element] = []
    for paragraph in div.iter(f"{{{TEI_NS}}}p"):
        for child in paragraph:
            if _local_name(child.tag) in TOKEN_TAGS:
                tokens.append(child)
    return tuple(tokens)


def _canonical_element(
    element: ET.Element,
    *,
    ignore_token_xml_lang: bool = False,
) -> str:
    is_token = _local_name(element.tag) in TOKEN_TAGS
    attributes = [
        (_local_name(name) if name not in {XML_ID, XML_LANG} else name, value)
        for name, value in element.attrib.items()
        if not (ignore_token_xml_lang and is_token and name == XML_LANG)
    ]
    children = [
        (
            _canonical_element(
                child,
                ignore_token_xml_lang=ignore_token_xml_lang,
            ),
            _normalise_text(child.tail),
        )
        for child in element
    ]
    payload: list[object] = [
        _local_name(element.tag),
        sorted(attributes),
        _normalise_text(element.text),
        children,
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _candidate_signature(
    div: ET.Element,
    *,
    ignore_token_xml_lang: bool = False,
) -> str:
    attributes = [
        (_local_name(name) if name not in {XML_ID, XML_LANG} else name, value)
        for name, value in div.attrib.items()
        if name != "change"
    ]
    children = [
        (
            _canonical_element(
                child,
                ignore_token_xml_lang=ignore_token_xml_lang,
            ),
            _normalise_text(child.tail),
        )
        for child in div
    ]
    payload: list[object] = [
        _local_name(div.tag),
        sorted(attributes),
        _normalise_text(div.text),
        children,
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _token_ids(div: ET.Element) -> tuple[str, ...]:
    return tuple(token.attrib.get(XML_ID, "") for token in _tokens(div))


def _token_kinds(div: ET.Element) -> tuple[str, ...]:
    return tuple(_local_name(token.tag) for token in _tokens(div))


def _token_text(div: ET.Element) -> tuple[str, ...]:
    return tuple(_normalise_text("".join(token.itertext())) for token in _tokens(div))


def _token_languages(div: ET.Element) -> tuple[str, ...]:
    return tuple(token.attrib.get(XML_LANG, "") for token in _tokens(div))


def _segmented_divs(root: ET.Element) -> tuple[ET.Element, ...]:
    return tuple(
        element
        for element in root.iter(f"{{{TEI_NS}}}div")
        if element.attrib.get("type") == "edition"
        and element.attrib.get("subtype") == "transcription_segmented"
    )


def _suppressed(candidate_count: int, selected_index: int | None) -> tuple[int, ...]:
    return tuple(
        index
        for index in range(candidate_count)
        if selected_index is None or index != selected_index
    )


def _resolve_zoor0453_override(
    candidates: tuple[ET.Element, ...],
    *,
    source_revision: str,
    source_changes: tuple[str, ...],
) -> SegmentationResolution:
    if source_revision != PINNED_IIP_REVISION:
        raise SegmentationConflictError(
            "zoor0453: source-history override is valid only for the pinned IIP revision"
        )
    if len(candidates) != 2 or source_changes != _ZOOR0453_CHANGES:
        raise SegmentationConflictError(
            "zoor0453: source-history override candidate/change shape no longer matches research"
        )
    if any(not _meaningfully_nonempty(candidate) for candidate in candidates):
        raise SegmentationConflictError(
            "zoor0453: source-history override requires two non-empty candidates"
        )

    first, second = candidates
    if (
        _token_ids(first) != _ZOOR0453_IDS
        or _token_ids(second) != _ZOOR0453_IDS
        or _token_kinds(first) != _ZOOR0453_KINDS
        or _token_kinds(second) != _ZOOR0453_KINDS
        or _token_text(first) != _ZOOR0453_TEXT
        or _token_text(second) != _ZOOR0453_TEXT
    ):
        raise SegmentationConflictError(
            "zoor0453: source-history override token shape no longer matches research"
        )
    if _candidate_signature(
        first,
        ignore_token_xml_lang=True,
    ) != _candidate_signature(
        second,
        ignore_token_xml_lang=True,
    ):
        raise SegmentationConflictError(
            "zoor0453: source-history override has conflicts beyond xml:lang"
        )
    if (
        _token_languages(first) != ("arc",) * len(_ZOOR0453_IDS)
        or _token_languages(second) != ("grc",) * len(_ZOOR0453_IDS)
    ):
        raise SegmentationConflictError(
            "zoor0453: source-history override language conflict no longer matches research"
        )

    return SegmentationResolution(
        selected_index=0,
        status="source_history_override",
        suppressed_indices=(1,),
        source_changes=source_changes,
        conflict_fields=("xml:lang",),
    )


def resolve_segmented_root(
    root: ET.Element,
    *,
    source_revision: str,
    record_id: str,
) -> SegmentationResolution:
    """Resolve segmented candidates from an already validated/repaired XML root."""

    candidates = _segmented_divs(root)
    source_changes = tuple(candidate.attrib.get("change", "") for candidate in candidates)

    if not candidates:
        return SegmentationResolution(
            selected_index=None,
            status="absent",
            suppressed_indices=(),
            source_changes=(),
            conflict_fields=(),
        )
    if len(candidates) == 1:
        return SegmentationResolution(
            selected_index=0,
            status="single",
            suppressed_indices=(),
            source_changes=source_changes,
            conflict_fields=(),
        )

    nonempty = tuple(
        index
        for index, candidate in enumerate(candidates)
        if _meaningfully_nonempty(candidate)
    )
    if len(nonempty) == 1:
        selected = nonempty[0]
        return SegmentationResolution(
            selected_index=selected,
            status="sole_nonempty",
            suppressed_indices=_suppressed(len(candidates), selected),
            source_changes=source_changes,
            conflict_fields=(),
        )
    if not nonempty:
        return SegmentationResolution(
            selected_index=None,
            status="all_empty",
            suppressed_indices=tuple(range(len(candidates))),
            source_changes=source_changes,
            conflict_fields=(),
        )

    signatures = tuple(_candidate_signature(candidates[index]) for index in nonempty)
    if len(set(signatures)) == 1:
        selected = nonempty[0]
        return SegmentationResolution(
            selected_index=selected,
            status="equivalent_duplicates",
            suppressed_indices=_suppressed(len(candidates), selected),
            source_changes=source_changes,
            conflict_fields=(),
        )

    if record_id == "zoor0453":
        return _resolve_zoor0453_override(
            candidates,
            source_revision=source_revision,
            source_changes=source_changes,
        )

    raise SegmentationConflictError(
        f"{record_id}: non-equivalent duplicate transcription_segmented editions"
    )


def resolve_segmented_editions(
    path: Path,
    *,
    source_revision: str,
) -> SegmentationResolution:
    """Resolve duplicate segmented editions in one IIP XML record."""

    root = ET.parse(path).getroot()
    record_id = root.attrib.get(XML_ID) or path.stem
    return resolve_segmented_root(
        root,
        source_revision=source_revision,
        record_id=record_id,
    )
