"""Audit Brown IIP controlled taxonomies without changing source classifications.

The output is a reproducible diagnostic report, not a semantic sidecar.
Do not reinterpret raw source values or use labels to guess a category.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

PINNED_TAXONOMY_BLOB = "c273ee4f0c8e751fca3274c7ce2d1e6ec5d60637"
PINNED_SOURCE_REVISION = "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"
# Observed from the authenticated full 5,535-record Brown corpus in CI #176.
# These classify *source attribute occurrences*, not distinct inscriptions.
EXPECTED_PINNED_MULTIVALUE = {
    "fully_resolved": 402,
    "partially_resolved": 126,
    "no_resolved": 2,
}

_TEI = "http://www.tei-c.org/ns/1.0"
_XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_NS = {"tei": _TEI}
FEATURE_TAXONOMIES = {
    "object_type": "IIP-form",
    "material": "IIP-materials",
    "genre": "IIP-genre",
    "condition": "IIP-preservation",
    "religion": "IIP-religion",
}
EXPECTED_TAXONOMIES = frozenset(
    {
        "IIP-form",
        "IIP-materials",
        "IIP-genre",
        "IIP-preservation",
        "IIP-writing",
        "IIP-religion",
    }
)


class TaxonomyError(ValueError):
    """Pinned taxonomy source or deterministic resolution failed."""


@dataclass(frozen=True)
class TaxonomyRegistry:
    """Active TEI categories by taxonomy, mapped to human-readable labels."""

    taxonomies: dict[str, dict[str, str]]


def git_blob_sha(content: bytes) -> str:
    """Check the Git *blob-object* identity, not raw file SHA-1."""
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def parse_taxonomies(
    content: bytes,
    *,
    expected_blob: str | None = None,
) -> TaxonomyRegistry:
    """Parse active XML, not commented-out category-looking text."""
    if expected_blob is not None and git_blob_sha(content) != expected_blob:
        raise TaxonomyError("pinned taxonomy Git blob mismatch")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise TaxonomyError("malformed pinned taxonomy XML") from exc
    if root.tag != f"{{{_TEI}}}classDecl":
        raise TaxonomyError("unexpected taxonomy root or namespace")

    seen: set[str] = set()
    taxonomies: dict[str, dict[str, str]] = {}
    for taxonomy in list(root):
        if taxonomy.tag != f"{{{_TEI}}}taxonomy":
            raise TaxonomyError("unsupported taxonomy namespace or root child")
        taxonomy_id = taxonomy.attrib.get(_XML_ID)
        if not taxonomy_id or taxonomy_id in taxonomies:
            raise TaxonomyError("missing or duplicate taxonomy ID")
        if taxonomy_id not in EXPECTED_TAXONOMIES:
            raise TaxonomyError(f"unexpected taxonomy ID: {taxonomy_id}")
        categories: dict[str, str] = {}
        for category in taxonomy.iter(f"{{{_TEI}}}category"):
            category_id = category.attrib.get(_XML_ID)
            if not category_id or category_id in seen:
                raise TaxonomyError("missing or duplicate category ID")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", category_id):
                raise TaxonomyError("invalid category ID")
            seen.add(category_id)
            descriptions = category.findall("tei:catDesc", _NS)
            if len(descriptions) != 1:
                raise TaxonomyError(f"{category_id}: expected exactly one catDesc")
            label = " ".join("".join(descriptions[0].itertext()).split())
            if not label:
                raise TaxonomyError(f"{category_id}: empty category description")
            categories[category_id] = label
        if not categories:
            raise TaxonomyError(f"{taxonomy_id}: no active categories")
        taxonomies[taxonomy_id] = dict(sorted(categories.items()))

    if set(taxonomies) != EXPECTED_TAXONOMIES:
        raise TaxonomyError("missing one or more expected taxonomies")
    if expected_blob == PINNED_TAXONOMY_BLOB and len(seen) != 142:
        raise TaxonomyError(f"pinned taxonomy active count changed: {len(seen)} != 142")
    return TaxonomyRegistry(dict(sorted(taxonomies.items())))


def _resolution(registry: TaxonomyRegistry, feature: str, raw: str) -> dict[str, str]:
    taxonomy_id = FEATURE_TAXONOMIES[feature]
    if not raw or len(raw.split()) != 1:
        return {
            "status": "multiple_tokens" if raw and len(raw.split()) > 1 else "unresolved"
        }
    candidate = raw[1:] if raw.startswith("#") else raw
    if candidate in registry.taxonomies[taxonomy_id]:
        return {"status": "resolved", "category_id": candidate}
    if any(
        candidate in categories
        for other_taxonomy, categories in registry.taxonomies.items()
        if other_taxonomy != taxonomy_id
    ):
        return {"status": "wrong_taxonomy"}
    return {"status": "unresolved"}


def audit_values(
    registry: TaxonomyRegistry,
    observed: Mapping[str, Counter[str]],
) -> dict[str, Any]:
    """Return every distinct raw value and its status, without silent mapping."""
    if set(observed) != set(FEATURE_TAXONOMIES):
        raise TaxonomyError("missing or unexpected taxonomy-backed feature")
    fields: dict[str, dict[str, Any]] = {}
    total_multi: Counter[str] = Counter()
    for feature, taxonomy_id in sorted(FEATURE_TAXONOMIES.items()):
        rows: list[dict[str, Any]] = []
        statuses: Counter[str] = Counter()
        multi: Counter[str] = Counter()
        for raw, count in sorted(observed[feature].items()):
            if not isinstance(raw, str) or not isinstance(count, int) or count <= 0:
                raise TaxonomyError(f"{feature}: invalid raw value or count")
            resolution = _resolution(registry, feature, raw)
            status = resolution["status"]
            statuses[status] += count
            # TEI @ana/@class can be repeatable whitespace-separated IDREFS.
            # Analyze *each* token but keep the whole raw source field exact.
            token_data: list[dict[str, str | int]] = [
                {"index": index, "raw": token, **_resolution(registry, feature, token)}
                for index, token in enumerate(raw.split())
            ]
            if len(token_data) > 1:
                valid = sum(item["status"] == "resolved" for item in token_data)
                key = (
                    "fully_resolved" if valid == len(token_data)
                    else "partially_resolved" if valid else "no_resolved"
                )
                multi[key] += count
                total_multi[key] += count
            rows.append({"raw": raw, "count": count, **resolution, "tokens": token_data})
        fields[feature] = {
            "taxonomy_id": taxonomy_id,
            "observed_count": sum(observed[feature].values()),
            "distinct_value_count": len(rows),
            "resolved_count": statuses["resolved"],
            "unresolved_count": sum(
                n for status, n in statuses.items() if status != "resolved"
            ),
            "multivalue_resolution": {
                key: multi[key] for key in EXPECTED_PINNED_MULTIVALUE
            },
            "values": rows,
        }
    return {
        "source_revision": PINNED_SOURCE_REVISION,
        "taxonomy_git_blob": PINNED_TAXONOMY_BLOB,
        "taxonomy_count": len(registry.taxonomies),
        "active_category_count": sum(len(x) for x in registry.taxonomies.values()),
        "taxonomy_categories": {
            name: [
                {"id": category_id, "label": label}
                for category_id, label in categories.items()
            ]
            for name, categories in registry.taxonomies.items()
        },
        "fields": fields,
        "multivalue_resolution": {
            key: total_multi[key] for key in EXPECTED_PINNED_MULTIVALUE
        },
    }


def audit_native_taxonomies(
    api: Any, registry: TaxonomyRegistry, *, raw_original: bool = False,
) -> dict[str, Any]:
    """Query raw native TF feature items; never consult a metadata sidecar."""
    observed: dict[str, Counter[str]] = {}
    for feature in FEATURE_TAXONOMIES:
        values: Counter[str] = Counter()
        native_feature = feature + "_original" if raw_original else feature
        for _node, raw in api.Fs(native_feature).items():
            if not isinstance(raw, str):
                raise TaxonomyError(f"{feature}: unexpected non-text native TF feature")
            values[raw] += 1
        observed[feature] = values
    return audit_values(registry, observed)


def validate_native_normalization(
    api: Any, registry: TaxonomyRegistry,
) -> dict[str, Any]:
    """Independently reconcile every emitted canonical ID to original TF data.

    This intentionally reconstructs expectations from the *reloaded* native
    node features rather than consulting the converter's IR or audit counters.
    Missing values on either side, partial IDs and wrong node types fail.
    """
    inscriptions = set(api.F.otype.s("inscription"))
    normalized = 0
    unresolved: Counter[str] = Counter()

    for feature, taxonomy_id in FEATURE_TAXONOMIES.items():
        # Text-Fabric omits completely empty feature files, and Fs(name)
        # returns None for a missing file. Reconcile each side as an empty
        # map without losing the explicit cross-map provenance checks below.
        source_feature = api.Fs(feature + "_original")
        canonical_feature = api.Fs(feature)
        originals = dict(source_feature.items()) if source_feature is not None else {}
        actual = dict(canonical_feature.items()) if canonical_feature is not None else {}
        if not (originals.keys() <= inscriptions and actual.keys() <= inscriptions):
            raise TaxonomyError(f"{feature}: classification outside inscription nodes")
        if not actual.keys() <= originals.keys():
            raise TaxonomyError(f"{feature}: canonical value without original source")
        category_ids = registry.taxonomies[taxonomy_id]

        for node, raw in originals.items():
            if not isinstance(raw, str):
                raise TaxonomyError(f"{feature}: non-text original at node {node}")
            tokens = raw.split()
            ids = tuple(token.removeprefix("#") for token in tokens)
            valid = bool(ids) and all(token in category_ids for token in ids)
            expected = " ".join(ids) if valid else None

            if expected is None:
                if node in actual:
                    raise TaxonomyError(
                        f"{feature}: unresolved original has canonical value at {node}"
                    )
                unresolved[feature] += 1
            elif actual.get(node) != expected:
                raise TaxonomyError(
                    f"{feature}: source/canonical mismatch at inscription {node}"
                )
            else:
                normalized += 1

    return {
        "normalized_fields": normalized,
        "unresolved_fields": dict(sorted(unresolved.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("taxonomy_xml", type=Path)
    parser.add_argument("tf_dir", type=Path)
    parser.add_argument("report_json", type=Path)
    parser.add_argument(
        "--raw-original", action="store_true",
        help="audit the verbatim <feature>_original source fields, not canonical IDs",
    )
    parser.add_argument(
        "--revision", default=PINNED_SOURCE_REVISION,
        choices=[PINNED_SOURCE_REVISION],
    )
    args = parser.parse_args()
    registry = parse_taxonomies(
        args.taxonomy_xml.read_bytes(), expected_blob=PINNED_TAXONOMY_BLOB
    )
    api: Any = Fabric(locations=str(args.tf_dir), silent=True).loadAll(silent=True)
    if not api:
        raise TaxonomyError("cannot load native Text-Fabric corpus")
    report = audit_native_taxonomies(api, registry, raw_original=args.raw_original)
    if args.raw_original:
        report["native_normalization_integrity"] = validate_native_normalization(
            api, registry
        )
    if report["multivalue_resolution"] != EXPECTED_PINNED_MULTIVALUE:
        raise TaxonomyError(
            "pinned multi-valued source classification partition changed: "
            + json.dumps(report["multivalue_resolution"], sort_keys=True)
        )
    destination = args.report_json
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temp.write_text(content, encoding="utf-8")
        temp.replace(destination)
    finally:
        temp.unlink(missing_ok=True)
    print(
        f"Pinned IIP taxonomy audit: {report['active_category_count']} active "
        f"categories, {len(report['fields'])} raw feature inventories"
    )
    for feature, data in report["fields"].items():
        print(
            f"{feature}: {data['distinct_value_count']} distinct, "
            f"{data['unresolved_count']} unresolved source records"
        )
    print(
        "Pinned multi-valued source classifications: "
        + json.dumps(report["multivalue_resolution"], sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
