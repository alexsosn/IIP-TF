"""Pinned full-corpus native Text-Fabric validation for issue #5."""

from __future__ import annotations

import argparse
import gc
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.release_gate import (
    PINNED_EPIDOC_SOURCE_TREE,
    compare_tf_feature_hashes,
    inventory_source_files,
    require_empty_output_directory,
    require_source_tree_sha,
    validate_oslots_mapping,
    write_build_reports,
)
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

EXPECTED_PARSED = 5535
EXPECTED_SIGNS = 1466387
EXPECTED_NODES = 322860
EXPECTED_EDGES = 409785
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
        "responsibility": ("inscription",),
        "publication_id": ("inscription",),
        "publication_include": ("inscription",),
        "publication_availability": ("inscription",),
        "publication_licence": ("publication_availability",),
        "publication_paragraph": ("publication_licence",),
        "publication_reference": ("publication_licence", "publication_paragraph"),
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
        if F.otype.v(source) == "sign":
            raise SystemExit(f"cites edge originates from slot {source}")
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

    # Provenance must be source-explicit: XInclude does not confer authority.
    inscriptions = F.otype.s("inscription")
    responsibilities = F.otype.s("responsibility")
    includes = F.otype.s("publication_include")
    authorities = tuple(api.Fs("publication_authority").items())
    titles = tuple(api.Fs("source_title").items())
    if len(titles) != len(inscriptions) or len(responsibilities) != 5537:
        raise SystemExit("source titles/responsibility cardinality mismatch")
    if len(includes) != 3483 or len(authorities) != 2052:
        raise SystemExit("publication include/authority cardinality mismatch")
    if len(F.otype.s("publication_id")) != len(inscriptions):
        raise SystemExit("publication IDs are missing or duplicated")
    if len(F.otype.s("publication_availability")) != 3:
        raise SystemExit("explicit availability statements were not retained")
    if len(F.otype.s("publication_licence")) != 3:
        raise SystemExit("explicit licence declarations were not retained")
    if len(F.otype.s("publication_paragraph")) != 3:
        raise SystemExit("explicit licence paragraph nodes were not retained")
    if len(F.otype.s("publication_reference")) != 6:
        raise SystemExit("explicit licence reference nodes were not retained")
    source_include = (
        "http://cds.library.brown.edu/projects/iip/include_publicationStmt.xml"
    )
    for node in includes:
        if (
            F.include_href.v(node) != source_include
            or F.include_resolved.v(node) != "0"
            or not F.include_fallback_text.v(node)
        ):
            raise SystemExit(f"publication include {node}: invalid source pointer")
        owner = E.parent.f(node)[0]
        if F.publication_authority.v(owner) is not None:
            raise SystemExit(f"publication include {node}: invented explicit authority")
    for node in responsibilities:
        if (
            not F.agent_name.v(node)
            or F.agent_tag.v(node) not in {"name", "persName"}
        ):
            raise SystemExit(f"responsibility {node}: source agent was lost")
    role_ids = tuple(api.Fs("responsibility_role_source_id").items())
    if len(role_ids) != 579 or not all(
        F.otype.v(node) == "responsibility"
        and F.responsibility_construct.v(node) == "respStmt"
        and isinstance(source_id, str)
        and source_id
        for node, source_id in role_ids
    ):
        raise SystemExit(
            "source resp/@xml:id provenance count or type changed"
        )
    if sum(
        F.responsibility_construct.v(node) == "principal"
        for node in responsibilities
    ) != 1:
        raise SystemExit("source-specific principal record was not preserved")
    if sum(
        F.responsibility_role.v(node) == "Prinicipal Investigator"
        for node in responsibilities
    ) != 3445:
        raise SystemExit("original misspelled investigator roles were normalized away")

    return {
        "validated_responsibilities": len(responsibilities),
        "validated_responsibility_role_ids": len(role_ids),
        "validated_publication_ids": len(F.otype.s("publication_id")),
        "validated_unexpanded_includes": len(includes),
        "validated_explicit_publication_authorities": len(authorities),
        "validated_explicit_licences": len(F.otype.s("publication_licence")),
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

    # Authenticate bytes against the upstream Git subtree, not a caller-supplied
    # provenance string or the agreement of two builds from identical inputs.
    verified_source_tree = require_source_tree_sha(
        args.source_dir, expected_sha=PINNED_EPIDOC_SOURCE_TREE
    )
    selected, excluded = inventory_source_files(args.source_dir, source_revision=args.revision)
    if len(selected) != EXPECTED_PARSED or excluded != {
        "aaTestFile.xml": "pinned source test fixture"
    }:
        raise SystemExit("pinned source file accounting changed")
    reports_dir = args.output_dir.with_name(args.output_dir.name + "-reports")
    # Refuse rather than erase any previous research output.
    require_empty_output_directory(reports_dir)

    irs = []
    node_counts: Counter[str] = Counter()
    edge_counts: Counter[str] = Counter()
    slot_languages: Counter[str] = Counter()
    slot_kinds: Counter[str] = Counter()
    sign_count = 0
    point_count = 0
    empty_structural = 0
    token_identities = 0

    for path in selected:
        ir = parse_epidoc_file(path, source_revision=args.revision)
        irs.append(ir)
        sign_count += len(ir.signs)
        for sign in ir.signs:
            slot_languages[sign.lang or "und"] += 1
            slot_kinds[sign.synthetic_kind or "visible"] += 1
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

    require_empty_output_directory(args.output_dir)
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

    validated_oslots_nodes = validate_oslots_mapping(
        api.E.oslots.items(),
        sign_count=sign_count,
        node_count=node_count,
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
        "validated_oslots_nodes": validated_oslots_nodes,
    }
    # Rebuild from source in a separate fresh directory, not the cached
    # in-memory canonical IR. Compare every native TF feature bytewise.
    # Drop first-build memory before the independent parse of 5,535 files.
    irs.clear()
    del api
    gc.collect()
    with tempfile.TemporaryDirectory(
        prefix="pinned-tf-independent-",
        dir=args.output_dir.parent,
    ) as fresh_directory:
        second_dir = Path(fresh_directory)
        write_tf_corpus(
            (parse_epidoc_file(path, source_revision=args.revision) for path in selected),
            second_dir,
            converter_commit=args.converter_commit,
        )
        feature_hashes = compare_tf_feature_hashes(args.output_dir, second_dir)
    if len(feature_hashes) != report["tf_files"]:
        raise SystemExit("not all native TF features were hashed")

    complete = {
        **report,
        "status": "success",
        "source_revision": args.revision,
        "verified_source_tree_git_sha1": verified_source_tree,
        "converter_commit": args.converter_commit,
        "source_files": {
            "converted": [path.name for path in selected],
            "excluded": excluded,
            "failed": [],
        },
        "slot_languages": dict(sorted(slot_languages.items())),
        "slot_kinds": dict(sorted(slot_kinds.items())),
        "tf_feature_hashes": feature_hashes,
        "reproducible_builds": 2,
    }
    write_build_reports(reports_dir, complete)
    print(json.dumps(complete, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
