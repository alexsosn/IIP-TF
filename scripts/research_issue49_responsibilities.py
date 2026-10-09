"""Inventory pinned Brown titleStmt responsibility and publication shapes (#49)."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from iip_tf.source_repair import repair_source_file

TEI = "{http://www.tei-c.org/ns/1.0}"
XI = "{http://www.w3.org/2001/XInclude}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _shape(element: ET.Element) -> str:
    children = ",".join(_local(child.tag) for child in element)
    attrs = ",".join(sorted(_local(name) for name in element.attrib))
    return f"{_local(element.tag)}[{attrs}]({children})"


def _text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    parsed = 0
    counters: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    child_shapes: Counter[str] = Counter()
    statement_shapes: Counter[str] = Counter()
    anomalies: list[dict[str, object]] = []
    samples: dict[str, dict[str, object]] = {}

    for path in sorted(args.source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        repaired = repair_source_file(path, source_revision=args.revision)
        root = ET.fromstring(repaired.text)
        parsed += 1
        title = root.find(f"./{TEI}teiHeader/{TEI}fileDesc/{TEI}titleStmt")
        if title is None:
            counters["records_without_titleStmt"] += 1
            continue
        counters["records_with_titleStmt"] += 1
        for child in title:
            counters[f"titleStmt_child:{_local(child.tag)}"] += 1
            child_shapes[_shape(child)] += 1

        statements = title.findall(f"./{TEI}respStmt")
        if len(statements) > 1:
            counters["records_with_multiple_respStmt"] += 1
        for statement in statements:
            counters["respStmt_count"] += 1
            statement_shapes[_shape(statement)] += 1
            responsibilities = statement.findall(f"./{TEI}resp")
            names = [
                child for child in statement
                if _local(child.tag) in {"name", "persName"}
            ]
            for role in responsibilities:
                role_counts[_text(role)] += 1
            for name in names:
                counters[f"agent_tag:{_local(name.tag)}"] += 1
                child_shapes[_shape(name)] += 1

            signature = _shape(statement)
            if signature not in samples:
                samples[signature] = {
                    "record": path.name,
                    "roles": [_text(role) for role in responsibilities],
                    "agents": [
                        {"tag": _local(name.tag), "text": _text(name),
                         "attrs": dict(name.attrib)}
                        for name in names
                    ],
                }

            other_children = [
                _local(child.tag) for child in statement
                if _local(child.tag) not in {"resp", "name", "persName"}
            ]
            if (len(responsibilities) != 1 or len(names) != 1 or other_children) and len(anomalies) < 60:
                anomalies.append({
                    "record": path.name,
                    "shape": signature,
                    "roles": [_text(role) for role in responsibilities],
                    "agents": [_text(name) for name in names],
                    "other_children": other_children,
                })

        publication = root.find(
            f"./{TEI}teiHeader/{TEI}fileDesc/{TEI}publicationStmt"
        )
        if publication is not None:
            for child in publication:
                name = _local(child.tag)
                counters[f"publicationStmt_child:{name}"] += 1
                if child.tag == f"{TEI}authority":
                    counters[f"publication_authority_text:{_text(child)}"] += 1
                elif child.tag == f"{XI}include":
                    counters["unexpanded_publication_xinclude"] += 1

    report = {
        "parsed": parsed,
        "counts": dict(sorted(counters.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "title_and_agent_shapes": dict(sorted(child_shapes.items())),
        "respStmt_shapes": dict(sorted(statement_shapes.items())),
        "sample_per_respStmt_shape": dict(sorted(samples.items())),
        "anomalies": anomalies,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    if parsed != 5535:
        raise SystemExit(f"unexpected parsed source count: {parsed} != 5535")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
