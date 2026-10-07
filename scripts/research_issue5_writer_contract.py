"""Audit the native TF writer contract against canonical IR for issue #5."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from iip_tf.ir import EdgeType, Layer, NodeType
from iip_tf.text_parser import parse_epidoc_file

SELECTED_ROLES = {
    "normalized": frozenset({"both", "normalized"}),
    "source": frozenset({"both", "source"}),
}
SCHEMA_INT_FEATURES = frozenset(
    {
        "line_n",
        "quantity_int",
        "date_not_before_int",
        "date_not_after_int",
        "candidate_index",
        "selected",
        "token_count",
    }
)


def _selection_hazards(signs, *, roles: frozenset[str]) -> tuple[int, int, list[dict[str, object]]]:
    selected = [i for i, sign in enumerate(signs) if sign.reading_role in roles]
    transfer = 0
    ambiguous = 0
    examples: list[dict[str, object]] = []

    for left, right in zip(selected, selected[1:]):
        interval = signs[left:right]
        nonempty = [(i + left, sign.after) for i, sign in enumerate(interval) if sign.after]
        if not nonempty:
            continue
        direct = signs[left].after
        last = nonempty[-1][1]
        if not direct and last:
            transfer += 1
            if len(examples) < 20:
                examples.append(
                    {
                        "left": left,
                        "right": right,
                        "left_role": signs[left].reading_role,
                        "right_role": signs[right].reading_role,
                        "suppressed": [
                            {
                                "index": i,
                                "role": signs[i].reading_role,
                                "glyph": signs[i].glyph,
                                "after": signs[i].after,
                                "synthetic_kind": signs[i].synthetic_kind,
                            }
                            for i in range(left + 1, right)
                        ],
                        "transfer_after": last,
                    }
                )
        values = {value for _, value in nonempty}
        if len(values) > 1 or len(nonempty) > 1:
            ambiguous += 1

    return transfer, ambiguous, examples


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    parsed = 0
    sign_count = 0
    node_count = 0
    edge_count = 0
    role_counts: Counter[str] = Counter()
    role_mix_records: Counter[str] = Counter()
    after_values: Counter[str] = Counter()
    hazards: Counter[str] = Counter()
    hazard_examples: dict[str, list[dict[str, object]]] = defaultdict(list)
    node_feature_types: dict[str, set[str]] = defaultdict(set)
    node_feature_domains: dict[str, set[str]] = defaultdict(set)
    edge_counts: Counter[str] = Counter()
    node_type_counts: Counter[str] = Counter()
    global_keys: set[str] = set()
    duplicate_global_keys: list[str] = []
    point_nodes = 0
    empty_structural = 0

    for path in sorted(args.source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        ir = parse_epidoc_file(path, source_revision=args.revision)
        parsed += 1
        sign_count += len(ir.signs)
        node_count += len(ir.nodes)
        edge_count += len(ir.edges)

        for sign in ir.signs:
            role_counts[f"{sign.layer.value}:{sign.reading_role}"] += 1
            if sign.after:
                after_values[repr(sign.after)] += 1
            if sign.key in global_keys:
                duplicate_global_keys.append(sign.key)
            global_keys.add(sign.key)

        for layer in Layer:
            layer_signs = [sign for sign in ir.signs if sign.layer == layer]
            if not layer_signs:
                continue
            roles = {sign.reading_role for sign in layer_signs}
            if "normalized" in roles and "source" in roles:
                role_mix_records[layer.value] += 1
            for mode, allowed in SELECTED_ROLES.items():
                transfer, ambiguous, examples = _selection_hazards(layer_signs, roles=allowed)
                key = f"{layer.value}:{mode}"
                hazards[f"{key}:separator_transfer"] += transfer
                hazards[f"{key}:multi_separator_interval"] += ambiguous
                for example in examples:
                    if len(hazard_examples[key]) < 20:
                        hazard_examples[key].append(
                            {"record": ir.identity.inscription_id, **example}
                        )

        for node in ir.nodes:
            node_type_counts[node.node_type.value] += 1
            if node.key in global_keys:
                duplicate_global_keys.append(node.key)
            global_keys.add(node.key)
            if node.point_index is not None:
                point_nodes += 1
            elif not node.sign_keys and node.node_type in {NodeType.EDITION, NodeType.PARAGRAPH}:
                empty_structural += 1
            for name, value in node.features:
                node_feature_types[name].add("int" if isinstance(value, int) else "str")
                node_feature_domains[name].add(node.node_type.value)

        for edge in ir.edges:
            edge_counts[edge.edge_type.value] += 1

    mixed_feature_types = {
        name: sorted(types)
        for name, types in node_feature_types.items()
        if len(types) > 1
    }
    unexpected_int_features = sorted(
        name
        for name, types in node_feature_types.items()
        if "int" in types and name not in SCHEMA_INT_FEATURES
    )
    expected_int_as_string = sorted(
        name
        for name in SCHEMA_INT_FEATURES
        if name in node_feature_types and node_feature_types[name] != {"int"}
    )

    report = {
        "parsed": parsed,
        "sign_count": sign_count,
        "node_count": node_count,
        "edge_count": edge_count,
        "role_counts": dict(sorted(role_counts.items())),
        "records_with_both_reading_branches_by_layer": dict(sorted(role_mix_records.items())),
        "after_values": dict(sorted(after_values.items())),
        "selection_hazards": dict(sorted(hazards.items())),
        "selection_hazard_examples": dict(sorted(hazard_examples.items())),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "node_feature_types": {
            name: sorted(types) for name, types in sorted(node_feature_types.items())
        },
        "node_feature_domains": {
            name: sorted(domains) for name, domains in sorted(node_feature_domains.items())
        },
        "mixed_feature_types": mixed_feature_types,
        "unexpected_int_features": unexpected_int_features,
        "expected_int_as_string": expected_int_as_string,
        "edge_counts": dict(sorted(edge_counts.items())),
        "point_nodes": point_nodes,
        "empty_structural_nodes": empty_structural,
        "duplicate_global_key_count": len(duplicate_global_keys),
        "duplicate_global_keys": duplicate_global_keys[:50],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return int(
        bool(
            duplicate_global_keys
            or mixed_feature_types
            or unexpected_int_features
            or expected_int_as_string
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
