"""Researcher-facing labels for exact IIP source taxonomy IDREFs.

Uses the existing source-authenticated taxonomy registry. A dotted ID prefix
is only a naming candidate, never a documented TEI parent or ontology edge.
"""

from __future__ import annotations

from typing import Any

from iip_tf.taxonomy_audit import (
    FEATURE_TAXONOMIES,
    TaxonomyError,
    TaxonomyRegistry,
)


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
            parts = candidate.split(".")
            for length in range(len(parts) - 1, 0, -1):
                prefix = ".".join(parts[:length])
                if prefix in categories:
                    entry["dotted_prefix_candidate"] = prefix
                    break
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
