"""Canonical IIP metadata category IDs backed by Brown source taxonomies.

Only source-listed active category IDs may replace raw classification values.
No spelling similarity, Unicode inference, category guessing or partial IDREF
resolution. Original metadata remains losslessly queryable on inscription nodes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import TypedDict

from iip_tf.ir import InscriptionIR, IRNode, NodeType
from iip_tf.taxonomy_audit import FEATURE_TAXONOMIES, TaxonomyRegistry


class TaxonomyResolutionAudit(TypedDict):
    normalized_fields: int
    unresolved_fields: dict[str, int]


def resolve_taxonomy_features(
    ir: InscriptionIR,
    registry: TaxonomyRegistry,
) -> tuple[InscriptionIR, TaxonomyResolutionAudit]:
    """Normalize only fully source-resolved INSCRIPTION IDREFS, retaining raw."""
    counts: Counter[str] = Counter()
    resolved_count = 0
    nodes: list[IRNode] = []
    for node in ir.nodes:
        if node.node_type != NodeType.INSCRIPTION:
            nodes.append(node)
            continue
        original = dict(node.features)
        features = dict(original)
        for field, taxonomy_id in FEATURE_TAXONOMIES.items():
            if f"{field}_original" in features:
                raise ValueError(f"{ir.identity.inscription_id}: {field} already resolved")
            raw = original.get(field)
            if raw is None:
                continue
            if not isinstance(raw, str):
                raise ValueError(f"{ir.identity.inscription_id}: {field} is not source text")
            # An exact source record may contain multiple IDREFS separated
            # by XML whitespace; a partial match is NOT a full classification.
            tokens = raw.split()
            known = registry.taxonomies[taxonomy_id]
            mapped = [
                token[1:] if token.startswith("#") else token
                for token in tokens
            ]
            features[f"{field}_original"] = raw
            if not tokens or any(candidate not in known for candidate in mapped):
                features.pop(field, None)
                counts[field] += 1
            else:
                features[field] = " ".join(mapped)
                resolved_count += 1
        nodes.append(replace(node, features=tuple(features.items())))
    return replace(ir, nodes=tuple(nodes)), {
        "normalized_fields": resolved_count,
        "unresolved_fields": dict(sorted(counts.items())),
    }
