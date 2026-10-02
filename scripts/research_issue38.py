"""Pinned-source research for metadata prose strictness (issue #38)."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Final

from iip_tf.source_repair import PINNED_IIP_REVISION, repair_source_file

TEI_NS: Final = "http://www.tei-c.org/ns/1.0"
XML_NS: Final = "http://www.w3.org/XML/1998/namespace"
NS: Final = {"tei": TEI_NS}

TARGETS: Final = {
    "support_p": ".//tei:objectDesc/tei:supportDesc/tei:support/tei:p",
    "condition_p": ".//tei:supportDesc/tei:condition/tei:p",
    "layout_p": ".//tei:objectDesc/tei:layoutDesc/tei:layout/tei:p",
    "origin_p": ".//tei:history/tei:origin/tei:p",
    "hand_p": ".//tei:physDesc/tei:handDesc/tei:handNote/tei:p",
    "dimension_height": ".//tei:dimensions/tei:height",
    "dimension_width": ".//tei:dimensions/tei:width",
    "dimension_depth": ".//tei:dimensions/tei:depth",
    "origin_date": ".//tei:history/tei:origin/tei:date",
    "origin_region": ".//tei:history/tei:origin/tei:placeName/tei:region",
    "origin_geog_name": ".//tei:history/tei:origin/tei:placeName/tei:geogName",
    "origin_geog_feat": ".//tei:history/tei:origin/tei:placeName/tei:geogFeat",
    "origin_geo": ".//tei:history/tei:origin/tei:placeName/tei:geo",
    "settlement_geo": ".//tei:history/tei:origin/tei:placeName/tei:settlement/tei:geo",
    "provenance_place": ".//tei:history/tei:provenance/tei:placeName",
    "bibl_scope": ".//tei:div[@type='bibliography']/tei:listBibl/tei:bibl/tei:biblScope",
    "decoration_ab": ".//tei:physDesc/tei:decoDesc/tei:decoNote/tei:ab",
    "decoration_locus": ".//tei:physDesc/tei:decoDesc/tei:decoNote/tei:locus",
    "facsimile_desc": ".//tei:surface/tei:desc",
    "facsimile_note": ".//tei:surface/tei:note",
    "image_credit_name": ".//tei:surface/tei:desc/tei:persName",
    "revision_change": ".//tei:teiHeader/tei:revisionDesc/tei:change",
}


def _local(name: str) -> str:
    if name == f"{{{XML_NS}}}id":
        return "xml:id"
    if name == f"{{{XML_NS}}}lang":
        return "xml:lang"
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def audit(source_dir: Path) -> dict[str, object]:
    counts = {name: 0 for name in TARGETS}
    records: dict[str, set[str]] = {name: set() for name in TARGETS}
    attrs: dict[str, Counter[str]] = {
        name: Counter() for name in TARGETS
    }
    direct_children: dict[str, Counter[str]] = {
        name: Counter() for name in TARGETS
    }
    descendant_elements: dict[str, Counter[str]] = {
        name: Counter() for name in TARGETS
    }
    descendant_attrs: dict[str, Counter[str]] = {
        name: Counter() for name in TARGETS
    }
    files_with_attrs: dict[str, set[str]] = defaultdict(set)
    files_with_children: dict[str, set[str]] = defaultdict(set)

    parsed = 0
    skipped_test = 0
    for path in sorted(source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            skipped_test += 1
            continue
        repaired = repair_source_file(
            path,
            source_revision=PINNED_IIP_REVISION,
        )
        root = ET.fromstring(repaired.text)
        parsed += 1

        for label, xpath in TARGETS.items():
            elements = root.findall(xpath, NS)
            if not elements:
                continue
            records[label].add(path.name)
            counts[label] += len(elements)
            for element in elements:
                for raw_name in element.attrib:
                    attrs[label][_local(raw_name)] += 1
                    files_with_attrs[label].add(path.name)
                children = list(element)
                if children:
                    files_with_children[label].add(path.name)
                for child in children:
                    direct_children[label][_local(child.tag)] += 1
                for descendant in element.iter():
                    if descendant is element:
                        continue
                    tag = _local(descendant.tag)
                    descendant_elements[label][tag] += 1
                    for raw_name in descendant.attrib:
                        descendant_attrs[label][
                            f"{tag}@{_local(raw_name)}"
                        ] += 1

    return {
        "source_revision": PINNED_IIP_REVISION,
        "parsed_non_test": parsed,
        "skipped_test": skipped_test,
        "paths": {
            label: {
                "xpath": TARGETS[label],
                "records": len(records[label]),
                "elements": counts[label],
                "attributes": dict(sorted(attrs[label].items())),
                "direct_children": dict(
                    sorted(direct_children[label].items())
                ),
                "descendant_elements": dict(
                    sorted(descendant_elements[label].items())
                ),
                "descendant_attributes": dict(
                    sorted(descendant_attrs[label].items())
                ),
                "files_with_attributes": sorted(files_with_attrs[label]),
                "files_with_children": sorted(files_with_children[label]),
            }
            for label in TARGETS
        },
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            audit(args.source_dir),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
