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



def _validate_native_metadata_queries(api: Any) -> dict[str, int]:
    """Exercise native metadata node ownership and feature lookups on real IIP TF."""

    F, E = api.F, api.E
    checks = {
        "bibl_scope": ("bibl",),
        "dimension": ("inscription", "hand"),
        "facsimile_surface": ("inscription", "facsimile_surface"),
        "image": ("inscription", "facsimile_surface"),
        "support_note": ("inscription",),
        "revision": ("inscription",),
        "decoration": ("inscription",),
    }
    for node_type, allowed_parents in checks.items():
        nodes = F.otype.s(node_type)
        if not nodes:
            raise SystemExit(f"native metadata is missing {node_type} nodes")
        for node in nodes:
            parents = E.parent.f(node)
            if len(parents) != 1 or F.otype.v(parents[0]) not in allowed_parents:
                raise SystemExit(
                    f"{node_type} {node}: invalid direct parent {parents!r}"
                )

    # Every citation target must remain a queryable native bibliographic node.
    citations = 0
    for source, targets in E.cites.items():
        if F.otype.v(source) not in {"edition", "textpart"}:
            raise SystemExit(f"cites edge has unexpected source {source}")
        for target in targets:
            if F.otype.v(target) != "bibl":
                raise SystemExit(f"cites edge has non-bibl target {target}")
            citations += 1
    if not citations:
        raise SystemExit("no native citations are queryable")

    dated = tuple(api.Fs("date_not_before_int").items())
    if not dated or not any(
        isinstance(year, int) and isinstance(api.Fs("date_not_before").v(n), str)
        for n, year in dated
    ):
        raise SystemExit("raw/typed date features are not jointly queryable")

    referenced_places = tuple(api.Fs("settlement_ref").items())
    if not referenced_places or not all(
        F.otype.v(n) == "inscription" and isinstance(ref, str)
        for n, ref in referenced_places
    ):
        raise SystemExit("inscription settlement references are not queryable")

    nested_surfaces = sum(
        1
        for node in F.otype.s("facsimile_surface")
        if F.otype.v(E.parent.f(node)[0]) == "facsimile_surface"
    )
    if not nested_surfaces:
        raise SystemExit("nested facsimile surfaces lost on serialization")

    return {
        "validated_bibl_scopes": len(F.otype.s("bibl_scope")),
        "validated_dimensions": len(F.otype.s("dimension")),
        "validated_images": len(F.otype.s("image")),
        "validated_nested_surfaces": nested_surfaces,
        "validated_citations": citations,
        "dated_inscriptions_with_typed_derivative": len(dated),
        "settlement_refs": len(referenced_places),
    }


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

    shutil.rmtree(args.output_dir / ".tf", ignore_errors=True)
    for path in args.output_dir.glob("*.tf"):
        if "@dateWritten=" in path.read_text(encoding="utf-8"):
            raise SystemExit(f"volatile dateWritten remains in {path.name}")

    metadata_queries = _validate_native_metadata_queries(api)
    report = {
        **actual,
        "metadata_queries": metadata_queries,
        "node_counts": dict(sorted(node_counts.items())),
        "edge_counts": dict(sorted(edge_counts.items())),
        "tf_files": len(tuple(args.output_dir.glob("*.tf"))),
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
