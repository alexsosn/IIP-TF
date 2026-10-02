"""Audit canonical IR nodes with empty semantic spans for issue #43."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from iip_tf.text_parser import parse_epidoc_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    parsed = 0
    total_empty = 0
    records_with_empty: set[str] = set()
    by_type: Counter[str] = Counter()
    by_kind: Counter[str] = Counter()
    by_layer: Counter[str] = Counter()
    by_annotation_source: Counter[str] = Counter()
    empty_segmented_token_ids: list[str] = []
    examples: dict[str, list[dict[str, object]]] = defaultdict(list)

    for path in sorted(args.source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        ir = parse_epidoc_file(path, source_revision=args.revision)
        parsed += 1
        for node in ir.nodes:
            if node.sign_keys:
                continue
            total_empty += 1
            records_with_empty.add(ir.identity.inscription_id)
            features = dict(node.features)
            node_type = node.node_type.value
            kind = str(features.get("kind", ""))
            layer = str(features.get("layer", ""))
            annotation_source = str(features.get("annotation_source", ""))

            by_type[node_type] += 1
            if kind:
                by_kind[f"{node_type}:{kind}"] += 1
            if layer:
                by_layer[f"{node_type}:{layer}"] += 1
            if annotation_source:
                by_annotation_source[f"{node_type}:{annotation_source}"] += 1
            token_id = features.get("token_id")
            if annotation_source == "transcription_segmented" and isinstance(token_id, str):
                empty_segmented_token_ids.append(token_id)

            bucket = node_type if not kind else f"{node_type}:{kind}"
            if len(examples[bucket]) < 12:
                examples[bucket].append(
                    {
                        "record": ir.identity.inscription_id,
                        "source_file": ir.identity.source_file,
                        "node_key": node.key,
                        "features": features,
                        "sign_count_record": len(ir.signs),
                    }
                )

    report = {
        "parsed": parsed,
        "total_empty_nodes": total_empty,
        "records_with_empty_nodes": len(records_with_empty),
        "by_type": dict(sorted(by_type.items())),
        "by_kind": dict(sorted(by_kind.items())),
        "by_layer": dict(sorted(by_layer.items())),
        "by_annotation_source": dict(sorted(by_annotation_source.items())),
        "empty_segmented_token_identity_count": len(empty_segmented_token_ids),
        "empty_segmented_token_identities": sorted(empty_segmented_token_ids),
        "examples": dict(sorted(examples.items())),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
