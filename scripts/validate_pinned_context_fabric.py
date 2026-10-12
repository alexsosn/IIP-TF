"""Full native TF / raw Context-Fabric / mmap parity for the pinned IIP corpus.

The caller must have completed the independent pinned native build, including
the reproducibility report. No source download, conversion or data publication.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from iip_tf.release_gate import tf_feature_hashes


class ParityError(RuntimeError):
    """A missing feature, changed value, failed loader or stale graph."""


def _value(value: Any) -> str | int | None:
    """Normalize numpy scalars without coercing strings into integers."""
    from numbers import Integral

    if value is None or isinstance(value, str):
        return value
    if isinstance(value, Integral):
        return int(value)
    raise ParityError(f"unexpected annotated value type: {type(value).__name__}")


def fingerprint_rows(
    rows: Iterable[tuple[int, Any]], *, kind: str, edge_values: bool = False
) -> dict[str, Any]:
    """Stream a canonical digest, including absent/empty values and edge-kind semantics."""
    if kind not in {"node", "edge"}:
        raise ParityError(f"invalid feature kind: {kind}")
    digest = hashlib.sha256()
    count = 0
    links = 0
    previous = 0
    digest.update(f"{kind}:valued={edge_values}\n".encode("ascii"))
    for raw_node, item in rows:
        node = int(raw_node)
        if node <= previous:
            raise ParityError(f"feature row order not strictly increasing at {node}")
        previous = node
        if kind == "node":
            encoded: Any = [node, _value(item)]
        elif isinstance(item, Mapping):
            if not edge_values:
                raise ParityError("unexpected valued edge in an unvalued feature")
            targets = sorted((int(target), _value(val)) for target, val in item.items())
            encoded = [node, targets]
            links += len(targets)
        else:
            if edge_values:
                raise ParityError("expected valued edge mapping, got target set")
            target_ids = sorted(int(target) for target in item)
            encoded = [node, target_ids]
            links += len(target_ids)
        digest.update(json.dumps(encoded, ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
        count += 1
    return {"count": count, "links": links, "sha256": digest.hexdigest()}


def _source_schema(directory: Path) -> tuple[dict[str, bool], dict[str, bool]]:
    nodes: dict[str, bool] = {}
    edges: dict[str, bool] = {}
    for file in sorted(directory.glob("*.tf")):
        if not file.is_file():
            continue
        with file.open(encoding="utf-8") as stream:
            first = stream.readline().strip()
            if first == "@config":
                continue
            if first not in {"@node", "@edge"}:
                raise ParityError(f"invalid TF feature header: {file.name}")
            if file.stem in {"otype", "oslots"}:
                continue
            valued = first == "@edge" and any(
                line.strip() == "@edgeValues"
                for line in stream
                if line.startswith("@")
            )
        (nodes if first == "@node" else edges)[file.stem] = valued
    if not nodes or not (directory / "otype.tf").is_file():
        raise ParityError("missing nonempty TF feature inventory")
    return nodes, edges


def _manifest(api: Any, nodes: dict[str, bool], edges: dict[str, bool]) -> dict[str, Any]:
    observed_nodes = set(api.Fall(warp=False))
    observed_edges = set(api.Eall(warp=False))
    if observed_nodes != set(nodes) or observed_edges != set(edges):
        raise ParityError(
            "feature inventory differs: "
            f"node_missing={sorted(set(nodes) - observed_nodes)}, "
            f"node_extra={sorted(observed_nodes - set(nodes))}, "
            f"edge_missing={sorted(set(edges) - observed_edges)}, "
            f"edge_extra={sorted(observed_edges - set(edges))}"
        )
    otype = api.F.otype
    result: dict[str, Any] = {
        "slot_type": otype.slotType,
        "max_slot": otype.maxSlot,
        "max_node": otype.maxNode,
        "features": {
            "warp:otype": fingerprint_rows(otype.items(), kind="node"),
            "warp:oslots": fingerprint_rows(api.E.oslots.items(), kind="edge"),
        },
    }
    for name in sorted(nodes):
        result["features"][f"node:{name}"] = fingerprint_rows(
            getattr(api.F, name).items(), kind="node"
        )
    for name, valued in sorted(edges.items()):
        result["features"][f"edge:{name}"] = fingerprint_rows(
            getattr(api.E, name).items(), kind="edge", edge_values=valued
        )
    return result


def compare_manifests(reference: dict[str, Any], actual: dict[str, Any]) -> None:
    for key in ("slot_type", "max_slot", "max_node"):
        if reference[key] != actual.get(key):
            raise ParityError(f"warp {key} changed")
    ref = reference["features"]
    got = actual.get("features", {})
    if set(ref) != set(got):
        raise ParityError(
            f"feature inventory mismatch: missing={sorted(set(ref) - set(got))}; "
            f"extra={sorted(set(got) - set(ref))}"
        )
    mismatched = [name for name in sorted(ref) if ref[name] != got[name]]
    if mismatched:
        raise ParityError(
            f"{len(mismatched)} fingerprint mismatches "
            f"(count/values/edges): {mismatched[:24]}"
        )


def validate_pinned_cfm(
    corpus: Path, native_report: Path, destination: Path
) -> dict[str, Any]:
    """Load the *same already validated* IIP TF artifact in all three runtimes."""
    from cfabric.core import Fabric as ContextFabric  # type: ignore[import-not-found]
    from tf.fabric import Fabric as NativeFabric  # type: ignore[import-untyped]

    if not native_report.is_file():
        raise ParityError("missing complete pinned native reproducibility report")
    report = json.loads(native_report.read_text(encoding="utf-8"))
    if report.get("status") != "success" or report.get("reproducible_builds") != 2:
        raise ParityError("native pinned build has not passed reproducibility gates")

    original = tf_feature_hashes(corpus)
    if report.get("tf_feature_hashes") != original:
        raise ParityError("corpus TF bytes do not match independent pinned build report")
    if (corpus / ".cfm").exists():
        raise ParityError("refusing preexisting, possibly stale .cfm cache")

    nodes, edges = _source_schema(corpus)
    t0 = time.monotonic()

    native = NativeFabric(locations=str(corpus), silent="deep").loadAll(silent="deep")
    if native is None or native is False:
        raise ParityError("native Text-Fabric failed to load")
    oracle = _manifest(native, nodes, edges)
    del native
    gc.collect()
    t_native = time.monotonic()

    raw_fabric = ContextFabric(locations=str(corpus), silent="deep")
    raw = raw_fabric.loadAll(silent="deep")
    if raw is None or raw is False or getattr(raw_fabric, "_loaded_from_cfm", False):
        raise ParityError("Context-Fabric raw .tf load failed or used a precompiled cache")
    compare_manifests(oracle, _manifest(raw, nodes, edges))
    t_raw = time.monotonic()

    if not raw_fabric.compile(silent="deep"):
        raise ParityError("Context-Fabric compiler failed")
    if not tuple((corpus / ".cfm").glob("*/meta.json")):
        raise ParityError("compiler omitted .cfm manifest")
    del raw, raw_fabric
    gc.collect()
    t_compile = time.monotonic()

    compiled_fabric = ContextFabric(locations=str(corpus), silent="deep")
    compiled = compiled_fabric.loadAll(silent="deep")
    if compiled is None or compiled is False:
        raise ParityError("fresh compiled Context-Fabric loader failed")
    if not getattr(compiled_fabric, "_loaded_from_cfm", False):
        raise ParityError("compiled Context-Fabric silently fell back to raw .tf")
    compare_manifests(oracle, _manifest(compiled, nodes, edges))
    del compiled, compiled_fabric
    gc.collect()
    t_compiled = time.monotonic()

    if tf_feature_hashes(corpus) != original:
        raise ParityError("Context-Fabric altered independently validated TF data")

    result = {
        "status": "success",
        "source_revision": report["source_revision"],
        "converter_commit": report["converter_commit"],
        "slot_type": oracle["slot_type"],
        "max_slot": oracle["max_slot"],
        "max_node": oracle["max_node"],
        "node_features": len(nodes),
        "edge_features": len(edges),
        "feature_fingerprints": oracle["features"],
        "tf_feature_hashes": original,
        "seconds": {
            "native": round(t_native - t0, 2),
            "context_fabric_raw": round(t_raw - t_native, 2),
            "compile": round(t_compile - t_raw, 2),
            "compiled_reload": round(t_compiled - t_compile, 2),
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("native_report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = validate_pinned_cfm(args.corpus, args.native_report, args.output)
    print(
        f"IIP complete CFM parity PASS: {result['max_node']} nodes, "
        f"{result['node_features']} node and {result['edge_features']} edge features"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
