"""Read-only census of Brown IIP empty <g ref> anchors for glyph policy #58.

Matches the parser's exact empty-glyph condition; no Unicode guesses or
changes to Text-Fabric text/slot/markup semantics.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from lxml import etree  # type: ignore[import-untyped]

from iip_tf.release_gate import (
    PINNED_EPIDOC_SOURCE_TREE,
    inventory_source_files,
    require_source_tree_sha,
)
from iip_tf.taxonomy_audit import PINNED_SOURCE_REVISION


class GlyphInventoryError(ValueError):
    """Missing, duplicate, invalid XML or unaccounted source glyphs."""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _layer(element: etree._Element) -> str:
    for ancestor in element.iterancestors():
        if isinstance(ancestor.tag, str) and _local(ancestor.tag) == "div":
            if ancestor.get("type") == "edition" and ancestor.get("subtype"):
                return str(ancestor.get("subtype"))
    return "unclassified"


def scan_glyph_xml(path: Path) -> dict[str, Any]:
    """Count source XML g elements using precisely the current EpiDoc parser rule.

    A g is empty iff its own element text has no non-space content AND it
    contains no element/other children. Tail text belongs to the parent.
    XML attributes are XML-decoded parser values, not lexical source bytes.
    """
    if path.is_symlink() or path.suffix != ".xml" or not path.is_file():
        raise GlyphInventoryError(f"invalid XML source file: {path.name}")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    try:
        root = etree.parse(str(path), parser)
    except (OSError, etree.XMLSyntaxError) as exc:
        raise GlyphInventoryError(f"cannot parse XML source: {path.name}") from exc
    refs: Counter[str] = Counter()
    layers: Counter[str] = Counter()
    unreferenced = 0
    filled = 0
    for element in root.iter():
        if not isinstance(element.tag, str) or _local(element.tag) != "g":
            continue
        source_ref = element.get("ref")
        empty = not ((element.text and element.text.strip()) or len(element))
        if empty:
            if source_ref is None or source_ref == "":
                unreferenced += 1
                continue
            refs[source_ref] += 1
            layers[_layer(element)] += 1
        elif source_ref is not None and source_ref != "":
            filled += 1
    return {
        "record": path.stem,
        "empty_referenced": sum(refs.values()),
        "empty_unreferenced": unreferenced,
        "filled_referenced": filled,
        "refs": dict(sorted(refs.items())),
        "layers": dict(sorted(layers.items())),
    }


def audit_glyph_sources(paths: Iterable[Path]) -> dict[str, Any]:
    """Deterministic inventory; never skip parse errors or duplicate record IDs."""
    source_paths = sorted(tuple(paths), key=lambda path: path.name)
    if not source_paths:
        raise GlyphInventoryError("no source XML files")
    records: set[str] = set()
    refs: Counter[str] = Counter()
    layers: Counter[str] = Counter()
    by_record: dict[str, int] = {}
    empty_unref = 0
    filled = 0
    for path in source_paths:
        if path.stem in records:
            raise GlyphInventoryError(f"duplicate source record id: {path.stem}")
        records.add(path.stem)
        result = scan_glyph_xml(path)
        refs.update(result["refs"])
        layers.update(result["layers"])
        empty_unref += result["empty_unreferenced"]
        filled += result["filled_referenced"]
        if result["empty_referenced"]:
            by_record[path.stem] = result["empty_referenced"]
    count = sum(refs.values())
    if sum(by_record.values()) != count or sum(layers.values()) != count:
        raise GlyphInventoryError("empty glyph source accounting failed")
    return {
        "source_records": len(records),
        "records_with_empty_references": len(by_record),
        "empty_referenced": count,
        "empty_unreferenced": empty_unref,
        "filled_referenced": filled,
        "distinct_refs": len(refs),
        "refs": dict(sorted(refs.items())),
        "layers": dict(sorted(layers.items())),
        "by_record": dict(sorted(by_record.items())),
    }


def audit_pinned_source(directory: Path, output: Path) -> dict[str, Any]:
    """Authenticate pinned Brown Git tree BEFORE excluding its test fixture."""
    verified_tree = require_source_tree_sha(directory, expected_sha=PINNED_EPIDOC_SOURCE_TREE)
    paths, excluded = inventory_source_files(directory, source_revision=PINNED_SOURCE_REVISION)
    if len(paths) != 5535 or excluded != {
        "aaTestFile.xml": "pinned source test fixture"
    }:
        raise GlyphInventoryError("pinned Brown XML file accounting changed")
    report = {
        "status": "success",
        "source_revision": PINNED_SOURCE_REVISION,
        "source_epidoc_git_tree": verified_tree,
        "excluded": dict(sorted(excluded.items())),
        **audit_glyph_sources(paths),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Complete pinned epidoc-files directory")
    parser.add_argument("output", type=Path, help="Diagnostic JSON output, not a TF sidecar")
    args = parser.parse_args(argv)
    report = audit_pinned_source(args.source, args.output)
    print(json.dumps({
        "source_records": report["source_records"],
        "empty_referenced": report["empty_referenced"],
        "records_with_empty_references": report["records_with_empty_references"],
        "filled_referenced": report["filled_referenced"],
        "empty_unreferenced": report["empty_unreferenced"],
        "distinct_refs": report["distinct_refs"],
        "refs": report["refs"],
        "layers": report["layers"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
