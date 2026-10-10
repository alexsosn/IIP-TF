"""Executable researcher examples over native IIP Text-Fabric, without sidecars.

Invoke with `python -m iip_tf.researcher_queries PATH_TO_TF [INSCRIPTION_ID ...]`.
This module presents native TF query results; it does not materialize corpus data.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

DEFAULT_INSCRIPTIONS = ("abil0001", "chor0001", "caes0260", "masa0286")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def feature_inventory(api: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Discover feature names in the *loaded* TF data rather than the schema."""
    discovered: dict[str, list[str]] = api.TF.explore(silent="deep", show=False)
    return (
        tuple(sorted(discovered["nodes"])),
        tuple(sorted(discovered["edges"])),
    )


def require_native_features(api: Any, names: tuple[str, ...]) -> None:
    """Fail closed if a documented feature name is misspelled or absent."""
    node_features, edge_features = feature_inventory(api)
    missing = sorted(set(names) - set(node_features) - set(edge_features))
    if missing:
        raise ValueError(f"missing native TF features: {', '.join(missing)}")


def _source_value(api: Any, feature: str, node: int, present: set[str]) -> Any:
    return api.Fs(feature).v(node) if feature in present else None


def inspect_corpus(api: Any, inscription_ids: tuple[str, ...]) -> dict[str, Any]:
    """Query exact IDs, text layers and source annotations in one native TF API.

    The values preserve source vocabulary. Raw language fields must not be
    interpreted as a normalized language classification (see issues #52–#55).
    """
    if not inscription_ids:
        raise ValueError("at least one inscription ID is required")
    node_features, edge_features = feature_inventory(api)
    present = set(node_features)
    for required in ("inscription_id", "source_file", "primary_layer"):
        if required not in present:
            raise ValueError(f"missing native TF features: {required}")

    F, L, S, T = api.F, api.L, api.S, api.T
    records: list[dict[str, Any]] = []

    for inscription_id in inscription_ids:
        if not _ID_RE.fullmatch(inscription_id):
            raise ValueError(f"invalid inscription ID: {inscription_id!r}")
        node = T.nodeFromSection((inscription_id,))
        if node is None or F.inscription_id.v(node) != inscription_id:
            raise ValueError(f"inscription not found: {inscription_id}")
        query = f"inscription inscription_id={inscription_id}"
        hits = S.search(query)
        if len(hits) != 1 or hits[0][0] != node:
            raise ValueError(f"exact native TF search did not uniquely match: {inscription_id}")

        markup = L.d(node, otype="markup")
        kinds = Counter(
            str(api.Fs("kind").v(m))
            for m in markup
            if "kind" in present and api.Fs("kind").v(m) is not None
        )
        refs = sorted(
            {
                str(api.Fs("ref").v(m))
                for m in markup
                if "ref" in present
                and "kind" in present
                and api.Fs("kind").v(m) == "glyph"
                and api.Fs("ref").v(m)
            }
        )
        records.append(
            {
                "inscription_id": inscription_id,
                "source_file": F.source_file.v(node),
                "source_title": _source_value(api, "source_title", node, present),
                "primary_layer": F.primary_layer.v(node),
                "raw_main_lang": _source_value(api, "main_lang", node, present),
                "region": _source_value(api, "region", node, present),
                "date_not_before": _source_value(api, "date_not_before", node, present),
                "settlement_ref": _source_value(api, "settlement_ref", node, present),
                "primary_text": T.text(node, fmt="text-orig-full").strip(),
                "translation_text": T.text(node, fmt="text-translation-full").strip(),
                "line_count": len(L.d(node, otype="line")),
                "markup_kinds": sorted(kinds),
                "markup_counts": dict(sorted(kinds.items())),
                "glyph_references": refs,
                "search_query": query,
                "search_hits": len(hits),
            }
        )

    provenance = F.inscription_id.meta
    metadata_types = (
        "bibl", "bibl_scope", "entity", "image", "facsimile_surface",
        "responsibility", "publication_include", "publication_licence",
    )
    return {
        "inscription_count": len(F.otype.s("inscription")),
        "source_revision": provenance.get("sourceCommit"),
        "data_licence": provenance.get("license"),
        "source_doi": provenance.get("sourceDOI"),
        "node_features": list(node_features),
        "edge_features": list(edge_features),
        "metadata_node_counts": {
            kind: len(F.otype.s(kind)) for kind in metadata_types
        },
        "records": records,
    }


def verify_pinned_examples(api: Any) -> dict[str, Any]:
    """Check researcher examples against the authenticated full Brown snapshot."""
    result = inspect_corpus(api, DEFAULT_INSCRIPTIONS)
    if result["inscription_count"] != 5535:
        raise ValueError("researcher examples did not load the pinned 5,535 inscriptions")
    records = {r["inscription_id"]: r for r in result["records"]}
    expected_kinds = {
        "abil0001": {"gap", "supplied", "unclear"},
        "caes0260": {"abbr", "ex"},
        "masa0286": {"glyph"},
    }
    for inscription_id, kinds in expected_kinds.items():
        if not kinds.issubset(set(records[inscription_id]["markup_kinds"])):
            raise ValueError(f"native editorial markup incomplete in {inscription_id}: {kinds}")
    if "phoen-gaml" not in records["masa0286"]["glyph_references"]:
        raise ValueError("pinned glyph reference is not queryable")
    if not records["chor0001"]["primary_text"]:
        raise ValueError("pinned visible primary reading is empty")
    if result["data_licence"] != "CC BY-NC 4.0":
        raise ValueError("source data licence not retained in native TF metadata")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tf_dir", type=Path, help="Directory containing native *.tf files")
    parser.add_argument("inscription_ids", nargs="*", default=list(DEFAULT_INSCRIPTIONS))
    args = parser.parse_args()
    tf_dir = args.tf_dir.resolve()
    if not tf_dir.is_dir():
        parser.error(f"native TF directory does not exist: {tf_dir}")
    api: Any = Fabric(locations=str(tf_dir), silent=True).loadAll(silent=True)
    if not api:
        raise RuntimeError("failed to load native TF features")
    result = inspect_corpus(api, tuple(args.inscription_ids))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
