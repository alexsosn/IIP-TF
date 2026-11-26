"""Research-only census of explicit IIP graphic refs against Brown image paths."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from iip_tf.release_gate import (
    PINNED_EPIDOC_SOURCE_TREE,
    inventory_source_files,
    require_source_tree_sha,
)
from iip_tf.source_repair import PINNED_IIP_REVISION, repair_source_file

IMAGE_REVISION = "7856b92502170b4ebfc974c09df2ab78e39804ff"
IMAGE_TREE = "8c5f4dc08cd31ed1fb8ae919c318206ffd5a67ab"
_TEI = {"tei": "http://www.tei-c.org/ns/1.0"}
_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._()-]*\.[A-Za-z0-9]+")


def image_paths_from_tree(tree: dict[str, Any], *, expected_sha: str) -> set[str]:
    """Accept the complete pinned flat tree of ordinary JPEG blobs only."""
    if tree.get("sha") != expected_sha or tree.get("truncated") is not False:
        raise ValueError("unexpected or incomplete image tree")
    entries = tree.get("tree")
    if not isinstance(entries, list) or not entries:
        raise ValueError("empty or invalid image tree")
    paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid image tree entry")
        path = entry.get("path")
        if (
            not isinstance(path, str)
            or not _FILENAME.fullmatch(path)
            or not path.endswith(".jpg")
            or entry.get("type") != "blob"
            or entry.get("mode") not in {"100644", "100755"}
            or path in paths
        ):
            raise ValueError(f"unexpected image tree entry: {path!r}")
        paths.add(path)
    return paths


def audit_facsimiles(source_dir: Path, image_paths: set[str]) -> dict[str, object]:
    """Measure exact source filename matches; do not infer missing references."""
    paths, excluded = inventory_source_files(
        source_dir, source_revision=PINNED_IIP_REVISION
    )
    counts: Counter[str] = Counter()
    unmatched: Counter[str] = Counter()
    unsupported: Counter[str] = Counter()
    exact_owners: dict[str, set[str]] = defaultdict(set)
    records_with_exact = 0
    repaired_files: list[str] = []
    for path in paths:
        repaired = repair_source_file(path, source_revision=PINNED_IIP_REVISION)
        if repaired.repaired:
            repaired_files.append(path.name)
        root = ET.fromstring(repaired.text)
        if root.tag != f"{{{_TEI['tei']}}}TEI":
            raise ValueError(f"unexpected source root: {path.name}")
        has_exact = False
        for facsimile in root.findall(".//tei:facsimile", _TEI):
            for graphic in facsimile.findall(".//tei:graphic", _TEI):
                value = graphic.get("url")
                if value is None:
                    counts["missing_attribute"] += 1
                elif value == "":
                    counts["empty"] += 1
                elif not _FILENAME.fullmatch(value):
                    counts["unsupported"] += 1
                    unsupported[value] += 1
                elif value in image_paths:
                    counts["exact"] += 1
                    exact_owners[value].add(path.name)
                    has_exact = True
                else:
                    counts["unmatched_filename"] += 1
                    unmatched[value] += 1
        records_with_exact += int(has_exact)
    return {
        "records": len(paths),
        "excluded": excluded,
        "repaired_files": repaired_files,
        "image_paths": len(image_paths),
        "graphic_occurrences": sum(counts.values()),
        "status_counts": dict(sorted(counts.items())),
        "records_with_exact": records_with_exact,
        "matched_filenames": sorted(exact_owners),
        "unreferenced_image_paths": sorted(image_paths - exact_owners.keys()),
        "shared_exact_refs": {
            name: sorted(owners)
            for name, owners in sorted(exact_owners.items())
            if len(owners) > 1
        },
        "unmatched_refs": dict(sorted(unmatched.items())),
        "unsupported_refs": dict(sorted(unsupported.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("image_tree", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    require_source_tree_sha(args.source_dir, expected_sha=PINNED_EPIDOC_SOURCE_TREE)
    tree = json.loads(args.image_tree.read_text(encoding="utf-8"))
    image_paths = image_paths_from_tree(tree, expected_sha=IMAGE_TREE)
    if len(image_paths) != 802:
        raise ValueError("unexpected pinned image path count")
    report = audit_facsimiles(args.source_dir, image_paths)
    report.update({
        "source_revision": PINNED_IIP_REVISION,
        "image_revision": IMAGE_REVISION,
        "image_tree": IMAGE_TREE,
    })
    if report["records"] != 5535:
        raise ValueError("unexpected pinned source record count")
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: report[key] for key in (
        "records", "image_paths", "graphic_occurrences", "status_counts",
        "records_with_exact",
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
