"""Deterministic corpus reconnaissance for the pinned IIP EpiDoc source."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NS}}}id"
XML_LANG = f"{{{XML_NS}}}lang"
IIP_DOI = "10.26300/pz1d-st89"
CC_BY_NC_MARKERS = (
    "creativecommons.org/licenses/by-nc/4.0",
    "attribution-noncommercial 4.0 international",
)
LOW_CARDINALITY_ATTRIBUTES = {
    "ana",
    "cert",
    "class",
    "extent",
    "mainLang",
    "otherLangs",
    "reason",
    "rend",
    "status",
    "subtype",
    "type",
    "unit",
    "xml:lang",
}
CONTAINER_ELEMENTS = {
    "TEI",
    "body",
    "div",
    "p",
    "text",
}
TOKEN_ELEMENTS = {"w", "num", "orig"}

Inventory = dict[str, Any]


def _local_name(name: str) -> str:
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def _attribute_name(name: str) -> str:
    if name == XML_LANG:
        return "xml:lang"
    if name == XML_ID:
        return "xml:id"
    return _local_name(name)


def _split_languages(value: str | None) -> list[str]:
    if not value:
        return []
    return [part for part in re.split(r"[\s,;]+", value.strip()) if part]


def _next_context(element: ET.Element, inherited: str) -> str:
    name = _local_name(element.tag)
    if name == "div":
        div_type = element.attrib.get("type", "")
        subtype = element.attrib.get("subtype", "")
        if div_type == "edition" and subtype in {"transcription", "transcription_segmented"}:
            return subtype
        if div_type in {"translation", "commentary", "bibliography"}:
            return div_type
        if div_type == "textpart":
            return "textpart"
    if name == "facsimile":
        return "facsimile"
    if name == "handDesc":
        return "hands"
    if name == "decoDesc":
        return "decorations"
    if name == "origin":
        return "origin"
    if name == "provenance":
        return "provenance"
    if name == "physDesc":
        return "physical_description"
    return inherited


def _walk_with_context(
    element: ET.Element,
    inherited: str = "other",
) -> Iterable[tuple[ET.Element, str]]:
    context = _next_context(element, inherited)
    yield element, context
    for child in element:
        yield from _walk_with_context(child, context)


def _is_meaningfully_nonempty(element: ET.Element) -> bool:
    if any(part.strip() for part in element.itertext()):
        return True
    for child in element.iter():
        if child is element:
            continue
        if _local_name(child.tag) not in {"div", "p", "lb", "pb", "cb"}:
            return True
    return False


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _nested_counter_dict(
    counters: dict[str, Counter[str]],
) -> dict[str, dict[str, int]]:
    return {
        context: _counter_dict(counters[context])
        for context in sorted(counters)
    }


def _record_has_license_marker(root: ET.Element, markers: tuple[str, ...]) -> bool:
    for element in root.iter():
        if _local_name(element.tag) != "licence":
            continue
        pieces = list(element.itertext())
        pieces.extend(str(value) for value in element.attrib.values())
        for descendant in element.iter():
            pieces.extend(str(value) for value in descendant.attrib.values())
        haystack = " ".join(pieces).lower()
        if any(marker in haystack for marker in markers):
            return True
    return False


def _record_has_iip_doi(root: ET.Element) -> bool:
    for element in root.iter():
        pieces = list(element.itertext())
        pieces.extend(str(value) for value in element.attrib.values())
        if IIP_DOI in " ".join(pieces):
            return True
    return False


def _is_test_or_non_inscription(path: Path, root: ET.Element) -> bool:
    lowered = path.name.lower()
    if "test" in lowered:
        return True
    return _local_name(root.tag) != "TEI"


def audit_directory(source_dir: Path, *, source_revision: str) -> Inventory:
    """Audit all top-level XML files in an IIP epidoc-files directory."""
    paths = sorted(source_dir.glob("*.xml"), key=lambda path: path.name)

    files = {
        "total_xml": len(paths),
        "parsed": 0,
        "malformed": 0,
        "test_or_non_inscription": 0,
    }
    malformed_examples: list[str] = []
    non_inscription_examples: list[str] = []

    record_languages: Counter[str] = Counter()
    token_languages: Counter[str] = Counter()
    element_counts: dict[str, Counter[str]] = defaultdict(Counter)
    attribute_counts: dict[str, Counter[str]] = defaultdict(Counter)
    attribute_values: dict[str, Counter[str]] = defaultdict(Counter)

    xml_ids: Counter[str] = Counter()
    iip_ids: Counter[str] = Counter()
    xml_id_files: dict[str, list[str]] = defaultdict(list)
    iip_id_files: dict[str, list[str]] = defaultdict(list)
    missing_xml_id: list[str] = []
    missing_iip_id: list[str] = []

    with_transcription = 0
    with_segmented = 0
    with_unsegmented_only = 0
    with_segmented_only = 0
    empty_transcription_records = 0
    records_with_textpart = 0
    line_break_elements = 0

    metadata_maxima = {
        "max_bibliography_entries_per_record": 0,
        "max_hand_notes_per_record": 0,
        "max_decorations_per_record": 0,
        "max_facsimile_surfaces_per_record": 0,
        "max_facsimile_graphics_per_record": 0,
        "max_revision_changes_per_record": 0,
    }

    records_with_any_licence = 0
    records_with_cc_by_nc = 0
    records_with_doi = 0

    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            files["malformed"] += 1
            if len(malformed_examples) < 25:
                malformed_examples.append(path.name)
            continue

        files["parsed"] += 1
        if _is_test_or_non_inscription(path, root):
            files["test_or_non_inscription"] += 1
            if len(non_inscription_examples) < 25:
                non_inscription_examples.append(path.name)

        xml_id = root.attrib.get(XML_ID)
        if xml_id:
            xml_ids[xml_id] += 1
            xml_id_files[xml_id].append(path.name)
        else:
            missing_xml_id.append(path.name)

        record_iip_ids = [
            (element.text or "").strip()
            for element in root.iter()
            if _local_name(element.tag) == "idno"
            and element.attrib.get("type") == "IIP"
            and (element.text or "").strip()
        ]
        if record_iip_ids:
            for identifier in set(record_iip_ids):
                iip_ids[identifier] += 1
                iip_id_files[identifier].append(path.name)
        else:
            missing_iip_id.append(path.name)

        transcription_divs: list[ET.Element] = []
        segmented_divs: list[ET.Element] = []
        has_textpart = False

        for element in root.iter():
            name = _local_name(element.tag)
            if name == "textLang":
                for language in _split_languages(element.attrib.get("mainLang")):
                    record_languages[language] += 1
                for language in _split_languages(element.attrib.get("otherLangs")):
                    record_languages[language] += 1
            if name in TOKEN_ELEMENTS:
                for language in _split_languages(element.attrib.get(XML_LANG)):
                    token_languages[language] += 1
            if name == "div":
                div_type = element.attrib.get("type")
                subtype = element.attrib.get("subtype")
                if div_type == "edition" and subtype == "transcription":
                    transcription_divs.append(element)
                elif div_type == "edition" and subtype == "transcription_segmented":
                    segmented_divs.append(element)
                if div_type == "textpart":
                    has_textpart = True

        if transcription_divs:
            with_transcription += 1
            if not any(_is_meaningfully_nonempty(div) for div in transcription_divs):
                empty_transcription_records += 1
            line_break_elements += sum(
                1
                for div in transcription_divs
                for element in div.iter()
                if _local_name(element.tag) == "lb"
            )
        if segmented_divs:
            with_segmented += 1
        if transcription_divs and not segmented_divs:
            with_unsegmented_only += 1
        if segmented_divs and not transcription_divs:
            with_segmented_only += 1
        if has_textpart:
            records_with_textpart += 1

        for element, context in _walk_with_context(root):
            name = _local_name(element.tag)
            element_counts[context][name] += 1
            for raw_attr, value in element.attrib.items():
                attr = _attribute_name(raw_attr)
                attribute_counts[context][f"{name}@{attr}"] += 1
                if attr in LOW_CARDINALITY_ATTRIBUTES and value.strip():
                    attribute_values[f"{name}@{attr}"][value.strip()] += 1

        per_record_counts = Counter(_local_name(element.tag) for element in root.iter())
        metadata_maxima["max_bibliography_entries_per_record"] = max(
            metadata_maxima["max_bibliography_entries_per_record"],
            per_record_counts["bibl"],
        )
        metadata_maxima["max_hand_notes_per_record"] = max(
            metadata_maxima["max_hand_notes_per_record"],
            per_record_counts["handNote"],
        )
        metadata_maxima["max_decorations_per_record"] = max(
            metadata_maxima["max_decorations_per_record"],
            per_record_counts["decoNote"],
        )
        metadata_maxima["max_facsimile_surfaces_per_record"] = max(
            metadata_maxima["max_facsimile_surfaces_per_record"],
            per_record_counts["surface"],
        )
        metadata_maxima["max_facsimile_graphics_per_record"] = max(
            metadata_maxima["max_facsimile_graphics_per_record"],
            per_record_counts["graphic"],
        )
        metadata_maxima["max_revision_changes_per_record"] = max(
            metadata_maxima["max_revision_changes_per_record"],
            per_record_counts["change"],
        )

        if any(_local_name(element.tag) == "licence" for element in root.iter()):
            records_with_any_licence += 1
        if _record_has_license_marker(root, CC_BY_NC_MARKERS):
            records_with_cc_by_nc += 1
        if _record_has_iip_doi(root):
            records_with_doi += 1

    duplicate_xml_ids = sorted(key for key, count in xml_ids.items() if count > 1)
    duplicate_iip_ids = sorted(key for key, count in iip_ids.items() if count > 1)
    duplicate_xml_id_files = {
        key: sorted(xml_id_files[key]) for key in duplicate_xml_ids
    }
    duplicate_iip_id_files = {
        key: sorted(iip_id_files[key]) for key in duplicate_iip_ids
    }

    inventory: Inventory = {
        "schema_version": 1,
        "source": {
            "repository": "Brown-University-Library/iip-texts",
            "revision": source_revision,
            "path": "epidoc-files",
        },
        "files": files,
        "diagnostics": {
            "malformed_examples": malformed_examples,
            "test_or_non_inscription_examples": non_inscription_examples,
        },
        "identity": {
            "distinct_xml_ids": len(xml_ids),
            "missing_xml_id_count": len(missing_xml_id),
            "missing_xml_id_examples": missing_xml_id[:25],
            "duplicate_xml_ids": duplicate_xml_ids[:100],
            "duplicate_xml_id_files": duplicate_xml_id_files,
            "distinct_iip_ids": len(iip_ids),
            "missing_iip_id_count": len(missing_iip_id),
            "missing_iip_id_examples": missing_iip_id[:25],
            "duplicate_iip_ids": duplicate_iip_ids[:100],
            "duplicate_iip_id_files": duplicate_iip_id_files,
        },
        "transcriptions": {
            "records_with_transcription": with_transcription,
            "records_with_segmented_transcription": with_segmented,
            "records_with_unsegmented_only": with_unsegmented_only,
            "records_with_segmented_only": with_segmented_only,
            "empty_transcription_records": empty_transcription_records,
        },
        "structure": {
            "records_with_textpart": records_with_textpart,
            "line_break_elements": line_break_elements,
        },
        "languages": {
            "record_declarations": _counter_dict(record_languages),
            "token_declarations": _counter_dict(token_languages),
        },
        "metadata": metadata_maxima,
        "licence": {
            "records_with_any_licence_element": records_with_any_licence,
            "records_with_cc_by_nc_4_0": records_with_cc_by_nc,
            "records_with_iip_doi": records_with_doi,
        },
        "elements": _nested_counter_dict(element_counts),
        "attributes": _nested_counter_dict(attribute_counts),
        "attribute_values": {
            key: _counter_dict(attribute_values[key])
            for key in sorted(attribute_values)
        },
    }
    return inventory


def _table(rows: Iterable[tuple[str, int]]) -> str:
    lines = ["| Construct | Count |", "|---|---:|"]
    lines.extend(f"| `{name}` | {count} |" for name, count in rows)
    return "\n".join(lines)


def _sorted_counts(values: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(values.items(), key=lambda item: (-item[1], item[0]))


def render_markdown(inventory: Inventory) -> str:
    """Render a compact researcher/maintainer report from the canonical inventory."""
    source = inventory["source"]
    files = inventory["files"]
    transcriptions = inventory["transcriptions"]
    structure = inventory["structure"]
    languages = inventory["languages"]
    metadata = inventory["metadata"]
    licence = inventory["licence"]
    elements = inventory["elements"]
    identity = inventory["identity"]

    lines = [
        "# IIP corpus audit",
        "",
        f"Source revision: `{source['revision']}`",
        "",
        "This report is generated from `iip-inventory.json`; counts are not hand-edited.",
        "",
        "## File accounting",
        "",
        f"- Total XML files: **{files['total_xml']}**",
        f"- Parsed: **{files['parsed']}**",
        f"- Malformed/unreadable: **{files['malformed']}**",
        f"- Test/non-inscription records: **{files['test_or_non_inscription']}**",
        "",
        "### Malformed/unreadable files",
        "",
    ]
    malformed = inventory["diagnostics"]["malformed_examples"]
    if malformed:
        lines.extend(f"- `{name}`" for name in malformed)
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Identity",
            "",
            f"- Distinct XML ids: **{identity['distinct_xml_ids']}**",
            f"- Missing XML ids: **{identity['missing_xml_id_count']}**",
            f"- Duplicate XML ids: **{len(identity['duplicate_xml_ids'])}**",
            f"- Distinct IIP ids: **{identity['distinct_iip_ids']}**",
            f"- Missing IIP ids: **{identity['missing_iip_id_count']}**",
            f"- Duplicate IIP ids: **{len(identity['duplicate_iip_ids'])}**",
            "",
            "### Duplicate XML identities",
            "",
        ]
    )
    duplicate_xml_files = identity["duplicate_xml_id_files"]
    if duplicate_xml_files:
        for identifier, filenames in sorted(duplicate_xml_files.items()):
            rendered = ", ".join(f"`{name}`" for name in filenames)
            lines.append(f"- `{identifier}`: {rendered}")
    else:
        lines.append("- None")

    lines.extend(["", "### Duplicate IIP identities", ""])
    duplicate_iip_files = identity["duplicate_iip_id_files"]
    if duplicate_iip_files:
        for identifier, filenames in sorted(duplicate_iip_files.items()):
            rendered = ", ".join(f"`{name}`" for name in filenames)
            lines.append(f"- `{identifier}`: {rendered}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Text and segmentation",
            "",
            f"- Records with transcription: **{transcriptions['records_with_transcription']}**",
            (
                "- Records with segmented transcription: "
                f"**{transcriptions['records_with_segmented_transcription']}**"
            ),
            (
                "- Records with transcription but no segmented transcription: "
                f"**{transcriptions['records_with_unsegmented_only']}**"
            ),
            (
                "- Records with segmented transcription but no source transcription: "
                f"**{transcriptions['records_with_segmented_only']}**"
            ),
            (
                "- Records whose transcription has no visible/source-bearing content: "
                f"**{transcriptions['empty_transcription_records']}**"
            ),
            f"- Records using explicit textpart: **{structure['records_with_textpart']}**",
            (
                "- Line-break elements in source transcriptions: "
                f"**{structure['line_break_elements']}**"
            ),
            "",
            "## Languages",
            "",
            "### Record-level textLang declarations",
            "",
            _table(_sorted_counts(languages["record_declarations"])),
            "",
            "### Token-level xml:lang declarations",
            "",
            _table(_sorted_counts(languages["token_declarations"])),
            "",
            "## Repeatable metadata maxima",
            "",
        ]
    )
    for key, value in sorted(metadata.items()):
        lines.append(f"- `{key}`: **{value}**")

    lines.extend(
        [
            "",
            "## Licence evidence",
            "",
            (
                "- Records containing a licence element: "
                f"**{licence['records_with_any_licence_element']}**"
            ),
            (
                "- Records explicitly matching CC BY-NC 4.0 markers: "
                f"**{licence['records_with_cc_by_nc_4_0']}**"
            ),
            (
                "- Records explicitly containing the IIP DOI: "
                f"**{licence['records_with_iip_doi']}**"
            ),
            "",
            (
                "These are per-record observations. A project-wide redistribution conclusion "
                "must not be inferred from a subset without separately checking authoritative "
                "project-level terms."
            ),
            "",
            "## Textual/editorial construct inventory",
            "",
        ]
    )

    for context in ("transcription", "transcription_segmented"):
        counts = elements.get(context, {})
        rows = [
            (name, count)
            for name, count in _sorted_counts(counts)
            if name not in CONTAINER_ELEMENTS
        ]
        lines.extend([f"### {context}", "", _table(rows), ""])

    rare: list[tuple[str, int]] = []
    for context in ("transcription", "transcription_segmented"):
        for name, count in elements.get(context, {}).items():
            if name not in CONTAINER_ELEMENTS and count <= 10:
                rare.append((f"{context}:{name}", count))

    lines.extend(
        [
            "## Rare schema-decision surface",
            "",
            (
                "The following textual/editorial constructs occur at most ten times in their "
                "context. Rarity does not make them ignorable; issue #3 must decide their native "
                "TF representation or explicitly classify them."
            ),
            "",
            _table(sorted(rare, key=lambda item: (item[1], item[0]))),
            "",
            "## Mapping implications for issue #3",
            "",
            (
                "1. Segmented and unsegmented coverage must be modelled separately; token "
                "boundaries may only be taken from source evidence."
            ),
            (
                "2. Every textual/editorial construct listed above needs an explicit mapping "
                "decision. The audit does not authorize silent dropping."
            ),
            (
                "3. Repeatable metadata whose observed per-record maximum exceeds one cannot be "
                "safely represented as a single scalar inscription feature without a loss rule."
            ),
            (
                "4. Licence/provenance features must preserve the pinned source revision and the "
                "verified upstream attribution requirements."
            ),
            "",
        ]
    )
    return "\n".join(lines)

def _json_text(inventory: Inventory) -> str:
    return json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _check_or_write(path: Path, content: str, *, check: bool) -> bool:
    if check:
        try:
            current = path.read_text(encoding="utf-8")
        except OSError:
            return False
        return current == content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a local IIP epidoc-files directory")
    parser.add_argument("source", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--markdown", dest="markdown_path", type=Path, required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated bytes with existing outputs instead of writing them",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inventory = audit_directory(args.source, source_revision=args.revision)
    json_ok = _check_or_write(args.json_path, _json_text(inventory), check=args.check)
    markdown_ok = _check_or_write(
        args.markdown_path,
        render_markdown(inventory) + "\n",
        check=args.check,
    )
    if args.check and not (json_ok and markdown_ok):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
