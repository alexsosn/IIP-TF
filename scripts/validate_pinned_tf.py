"""Pinned full-corpus native Text-Fabric validation for issue #5."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

EXPECTED_PARSED = 5535
EXPECTED_SIGNS = 1466387
EXPECTED_NODES = 308290
EXPECTED_EDGES = 380645
EXPECTED_POINTS = 49
EXPECTED_EMPTY_STRUCTURAL = 11427
EXPECTED_SEGMENTED_TOKEN_IDENTITIES = 39472


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--converter-commit", required=True)
    args = parser.parse_args()

    irs = []
    node_counts: Counter[str] = Counter()
    edge_counts: Counter[str] = Counter()
    sign_count = 0
    point_count = 0
    empty_structural = 0
    token_identities = 0

    for path in sorted(args.source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        ir = parse_epidoc_file(path, source_revision=args.revision)
        irs.append(ir)
        sign_count += len(ir.signs)
        for node in ir.nodes:
            node_counts[node.node_type.value] += 1
            if node.point_index is not None:
                point_count += 1
            elif not node.sign_keys and node.node_type in {
                NodeType.EDITION,
                NodeType.PARAGRAPH,
            }:
                empty_structural += 1
            if node.node_type == NodeType.WORD:
                token_identities += 1
            elif (
                node.node_type == NodeType.MARKUP
                and node.feature("annotation_source") == "transcription_segmented"
                and node.feature("token_id") is not None
                and not node.sign_keys
            ):
                token_identities += 1
        for edge in ir.edges:
            edge_counts[edge.edge_type.value] += 1

    parsed = len(irs)
    edge_count = sum(edge_counts.values())
    node_count = sum(node_counts.values())

    expected = {
        "parsed": EXPECTED_PARSED,
        "signs": EXPECTED_SIGNS,
        "nodes": EXPECTED_NODES,
        "edges": EXPECTED_EDGES,
        "points": EXPECTED_POINTS,
        "empty_structural": EXPECTED_EMPTY_STRUCTURAL,
        "segmented_token_identities": EXPECTED_SEGMENTED_TOKEN_IDENTITIES,
    }
    actual = {
        "parsed": parsed,
        "signs": sign_count,
        "nodes": node_count,
        "edges": edge_count,
        "points": point_count,
        "empty_structural": empty_structural,
        "segmented_token_identities": token_identities,
    }
    if actual != expected:
        raise SystemExit(
            "pinned canonical IR accounting changed: "
            + json.dumps({"expected": expected, "actual": actual}, sort_keys=True)
        )

    write_tf_corpus(
        tuple(irs),
        args.output_dir,
        converter_commit=args.converter_commit,
    )

    api: Any = Fabric(locations=str(args.output_dir), silent=True).loadAll(silent=True)
    if not api:
        raise SystemExit("Text-Fabric failed to load generated pinned corpus")

    loaded_node_counts = {
        node_type: len(api.F.otype.s(node_type))
        for node_type in ("sign", *sorted(node_counts))
    }
    if loaded_node_counts["sign"] != sign_count:
        raise SystemExit(
            f"loaded sign count {loaded_node_counts['sign']} != {sign_count}"
        )
    for node_type, count in node_counts.items():
        if loaded_node_counts[node_type] != count:
            raise SystemExit(
                f"loaded {node_type} count {loaded_node_counts[node_type]} != {count}"
            )

    loaded_edge_counts: dict[str, int] = {}
    for edge_type, expected_count in edge_counts.items():
        feature = api.Es(edge_type)
        count = sum(len(targets) for _, targets in feature.items())
        loaded_edge_counts[edge_type] = count
        if count != expected_count:
            raise SystemExit(
                f"loaded edge {edge_type} count {count} != {expected_count}"
            )

    point_nodes = tuple(node for node, _ in api.Fs("point_index").items())
    if len(point_nodes) != EXPECTED_POINTS:
        raise SystemExit(f"loaded point count {len(point_nodes)} != {EXPECTED_POINTS}")
    for node in point_nodes:
        slots = tuple(api.L.d(node, otype="sign"))
        if len(slots) != 1:
            raise SystemExit(f"point node {node} has {len(slots)} technical slots")
        relation = api.Fs("point_relation").v(node)
        if relation not in {"before", "after"}:
            raise SystemExit(f"point node {node} has invalid relation {relation!r}")

    empty_values = tuple(api.Fs("empty").items())
    if not empty_values:
        raise SystemExit("generated corpus lacks empty structural markers")

    for path in args.output_dir.glob("*.tf"):
        if "@dateWritten=" in path.read_text(encoding="utf-8"):
            raise SystemExit(f"volatile dateWritten remains in {path.name}")

    shutil.rmtree(args.output_dir / ".tf", ignore_errors=True)
    report = {
        **actual,
        "node_counts": dict(sorted(node_counts.items())),
        "edge_counts": dict(sorted(edge_counts.items())),
        "tf_files": len(tuple(args.output_dir.glob("*.tf"))),
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
