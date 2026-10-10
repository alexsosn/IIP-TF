"""Inventory pinned Brown titleStmt responsibility and publication shapes (#49)."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import TypedDict

from iip_tf.source_repair import repair_source_file


class ProvenanceAudit(TypedDict):
    parsed: int
    counts: dict[str, int]
    role_counts: dict[str, int]
    title_and_agent_shapes: dict[str, int]
    respStmt_shapes: dict[str, int]
    publicationStmt_shapes: dict[str, int]
    publication_child_shapes: dict[str, int]
    publication_include_hrefs: dict[str, int]
    sample_per_publication_child_shape: dict[str, dict[str, object]]
    sample_per_respStmt_shape: dict[str, dict[str, object]]
    anomalies: list[dict[str, object]]


TEI = "{http://www.tei-c.org/ns/1.0}"
XI = "{http://www.w3.org/2001/XInclude}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _shape(element: ET.Element) -> str:
    # Keep full Clark QNames in the research inventory: namespace aliasing
    # must not make an unaudited element look like a known TEI field.
    children = ",".join(child.tag for child in element)
    attrs = ",".join(sorted(element.attrib))
    return f"{element.tag}[{attrs}]({children})"


def _text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def audit(
    source_dir: Path, *, revision: str, expected_records: int = 5535
) -> ProvenanceAudit:
    """Measure contributor and publication provenance without normalization."""

    parsed = 0
    counters: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    child_shapes: Counter[str] = Counter()
    statement_shapes: Counter[str] = Counter()
    publication_shapes: Counter[str] = Counter()
    publication_child_shapes: Counter[str] = Counter()
    publication_includes: Counter[str] = Counter()
    publication_samples: dict[str, dict[str, object]] = {}
    anomalies: list[dict[str, object]] = []
    samples: dict[str, dict[str, object]] = {}

    for path in sorted(source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        repaired = repair_source_file(path, source_revision=revision)
        root = ET.fromstring(repaired.text)
        parsed += 1
        title = root.find(f"./{TEI}teiHeader/{TEI}fileDesc/{TEI}titleStmt")
        if title is None:
            counters["records_without_titleStmt"] += 1
            title = ET.Element("absent-titleStmt")
        else:
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
            is_anomalous = (
                len(responsibilities) != 1 or len(names) != 1 or bool(other_children)
            )
            if is_anomalous and len(anomalies) < 60:
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
        if publication is None:
            counters["records_without_publicationStmt"] += 1
        else:
            counters["records_with_publicationStmt"] += 1
            publication_shapes[_shape(publication)] += 1
            for child in publication:
                publication_child_name = _local(child.tag)
                counters[f"publicationStmt_child:{publication_child_name}"] += 1
                signature = _shape(child)
                publication_child_shapes[signature] += 1
                if signature not in publication_samples:
                    publication_samples[signature] = {
                        "record": path.name,
                        "text": _text(child),
                        "attrs": dict(child.attrib),
                    }
                if child.tag == f"{TEI}authority":
                    counters[f"publication_authority_text:{_text(child)}"] += 1
                elif child.tag == f"{XI}include":
                    counters["unexpanded_publication_xinclude"] += 1
                    publication_includes[child.attrib.get("href", "")] += 1

    report = {
        "parsed": parsed,
        "counts": dict(sorted(counters.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "title_and_agent_shapes": dict(sorted(child_shapes.items())),
        "respStmt_shapes": dict(sorted(statement_shapes.items())),
        "publicationStmt_shapes": dict(sorted(publication_shapes.items())),
        "publication_child_shapes": dict(sorted(publication_child_shapes.items())),
        "publication_include_hrefs": dict(sorted(publication_includes.items())),
        "sample_per_publication_child_shape": dict(sorted(publication_samples.items())),
        "sample_per_respStmt_shape": dict(sorted(samples.items())),
        "anomalies": anomalies,
    }
    if parsed != expected_records:
        raise ValueError(
            f"unexpected parsed source count: {parsed} != {expected_records}"
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expect-total", type=int, default=5535)
    args = parser.parse_args()

    report = audit(
        args.source_dir, revision=args.revision, expected_records=args.expect_total
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
