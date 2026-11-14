"""Researcher-facing labels for exact IIP source taxonomy IDREFs.

Uses the existing source-authenticated taxonomy registry. A dotted ID prefix
is only a naming candidate, never a documented TEI parent or ontology edge.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from iip_tf.taxonomy_audit import (
    FEATURE_TAXONOMIES,
    TaxonomyError,
    TaxonomyRegistry,
)


def _dotted_prefix_candidate(
    category_id: str, categories: Mapping[str, str],
) -> str | None:
    """Find a longest active name prefix without asserting TEI parentage."""
    parts = category_id.split(".")
    for length in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:length])
        if prefix in categories:
            return prefix
    return None


def catalog_taxonomies(
    registry: TaxonomyRegistry, taxonomy_id: str | None = None,
) -> dict[str, Any]:
    """List source-authenticated active TEI catDesc labels across all six scopes.

    The registry was already parsed and optionally pinned by
    taxonomy_audit.parse_taxonomies. All returned names are source values;
    dotted_prefix_candidate is textual only, never an authoritative edge.
    """
    if taxonomy_id is not None and taxonomy_id not in registry.taxonomies:
        raise TaxonomyError(f"unknown taxonomy ID: {taxonomy_id!r}")
    names = [taxonomy_id] if taxonomy_id is not None else sorted(registry.taxonomies)
    rows: list[dict[str, Any]] = []
    for name in names:
        categories = registry.taxonomies[name]
        entries: list[dict[str, str]] = []
        for category_id, label in sorted(categories.items()):
            entry = {"id": category_id, "label": label}
            prefix = _dotted_prefix_candidate(category_id, categories)
            if prefix is not None:
                entry["dotted_prefix_candidate"] = prefix
            entries.append(entry)
        rows.append({
            "taxonomy_id": name,
            "active_category_count": len(entries),
            "categories": entries,
        })
    return {
        "taxonomy_count": len(rows),
        "active_category_count": sum(row["active_category_count"] for row in rows),
        "label_source": "tei:catDesc",
        "relationship_policy": "dotted-prefix-candidates-only",
        "taxonomies": rows,
    }


def lookup_taxonomy_labels(
    registry: TaxonomyRegistry, feature: str, raw: str,
) -> dict[str, Any]:
    """Resolve each source IDREF independently, with source-scope evidence.

    Every original token is retained, including repetition and leading '#'.
    Partially resolved values remain partial; no canonical replacement is
    returned. XML-commented category-like strings cannot supply a label.
    """
    if feature not in FEATURE_TAXONOMIES:
        raise TaxonomyError(f"unsupported classification feature: {feature}")
    if not isinstance(raw, str):
        raise TaxonomyError("classification must be source text")
    taxonomy_id = FEATURE_TAXONOMIES[feature]
    categories = registry.taxonomies[taxonomy_id]
    tokens: list[dict[str, str | int]] = []
    resolved = 0

    for index, token in enumerate(raw.split()):
        candidate = token.removeprefix("#")
        entry: dict[str, str | int] = {"index": index, "raw": token}
        if candidate in categories:
            entry.update({
                "status": "resolved",
                "category_id": candidate,
                "label": categories[candidate],
            })
            resolved += 1
            # Dotted category IDs in Brown's source are sibling XML elements;
            # a matching prefix is *not* evidence of TEI parentage.
            prefix = _dotted_prefix_candidate(candidate, categories)
            if prefix is not None:
                entry["dotted_prefix_candidate"] = prefix
        elif any(
            candidate in other_categories
            for other_id, other_categories in registry.taxonomies.items()
            if other_id != taxonomy_id
        ):
            entry["status"] = "wrong_taxonomy"
        elif any(candidate.casefold() == known.casefold() for known in categories):
            entry["status"] = "case_mismatch"
        else:
            entry["status"] = "unknown"
        tokens.append(entry)

    resolution = (
        "fully_resolved" if tokens and resolved == len(tokens)
        else "partially_resolved" if resolved else "unresolved"
    )
    return {
        "feature": feature,
        "taxonomy_id": taxonomy_id,
        "raw": raw,
        "resolution": resolution,
        "tokens": tokens,
    }
