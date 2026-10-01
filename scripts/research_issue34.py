"""Research helper for issue #34 metadata source-shape inventory."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from iip_tf.source_repair import PINNED_IIP_REVISION, repair_source_file

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}


def _local(name: str) -> str:
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def _text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _surface_depth(surface: ET.Element, depth: int = 1) -> int:
    child_depths = [
        _surface_depth(child, depth + 1)
        for child in list(surface)
        if _local(child.tag) == "surface"
    ]
    return max([depth, *child_depths])


def audit(source_dir: Path) -> dict[str, object]:
    support_counts: dict[str, int] = {}
    nested_surface_depth: dict[str, int] = {}
    nested_surface_counts: dict[str, int] = {}

    for path in sorted(source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        repaired = repair_source_file(path, source_revision=PINNED_IIP_REVISION)
        root = ET.fromstring(repaired.text)

        support_ps = [
            child
            for support in root.findall(".//tei:objectDesc/tei:supportDesc/tei:support", NS)
            for child in list(support)
            if _local(child.tag) == "p" and _text(child)
        ]
        if support_ps:
            support_counts[path.name] = len(support_ps)

        surfaces = root.findall(".//tei:facsimile/tei:surface", NS)
        if surfaces:
            top_level = [
                surface
                for surface in surfaces
                if all(
                    surface is not child
                    for parent in surfaces
                    for child in list(parent)
                    if _local(child.tag) == "surface"
                )
            ]
            max_depth = max((_surface_depth(surface) for surface in top_level), default=1)
            nested = sum(
                1
                for surface in surfaces
                for child in list(surface)
                if _local(child.tag) == "surface"
            )
            if nested:
                nested_surface_depth[path.name] = max_depth
                nested_surface_counts[path.name] = nested

    repeated_support = {
        name: count for name, count in support_counts.items() if count > 1
    }
    return {
        "records_with_nonempty_support_p": len(support_counts),
        "max_nonempty_support_p_per_record": max(support_counts.values(), default=0),
        "records_with_repeated_support_p": repeated_support,
        "nested_surface_records": nested_surface_counts,
        "nested_surface_max_depth_by_record": nested_surface_depth,
        "max_surface_depth": max(nested_surface_depth.values(), default=1),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.source_dir), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
