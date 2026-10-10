"""Release-gate primitives: exact source accounting and TF byte reproducibility.

Reports and SHA manifests are build artifacts, never semantic sidecars.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path

from iip_tf.source_repair import PINNED_IIP_REVISION

_PINNED_EXCLUSIONS = {"aaTestFile.xml": "pinned source test fixture"}
# Brown-University-Library/iip-texts at PINNED_IIP_REVISION, /epidoc-files/.
# Verified from the upstream Git Trees API: 5,536 regular 100644 XML blobs.
PINNED_EPIDOC_SOURCE_TREE = "4445c4878873227c73ead5e8b94f9e3487c28c3b"


class ReproducibilityError(ValueError):
    """A TF corpus feature set is missing or differs byte-for-byte."""


def _git_blob_oid(path: Path) -> bytes:
    """Hash source bytes with Git's blob-object framing (SHA-1)."""
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.digest()


def git_source_tree_sha(source_dir: Path) -> str:
    """Reconstruct Git's flat tree ID for the complete original EpiDoc directory.

    The verified pinned subtree contains only ordinary 100644 XML blobs.
    Reject any added file, directory, or symlink rather than silently ignoring it.
    """
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise ReproducibilityError(f"invalid source tree directory: {source_dir}")
    paths = sorted(source_dir.iterdir(), key=lambda path: path.name.encode("utf-8"))
    if not paths:
        raise ReproducibilityError("source tree directory is empty")
    chunks: list[bytes] = []
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.suffix != ".xml":
            raise ReproducibilityError(f"unexpected source tree entry: {path.name}")
        chunks.append(b"100644 " + path.name.encode("utf-8") + b"\0" + _git_blob_oid(path))
    content = b"".join(chunks)
    return hashlib.sha1(b"tree " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def require_source_tree_sha(source_dir: Path, *, expected_sha: str) -> str:
    """Reject source trees that do not match a trusted upstream Git tree object."""
    observed = git_source_tree_sha(source_dir)
    if observed != expected_sha:
        raise ReproducibilityError(
            f"source tree identity mismatch: expected {expected_sha}, got {observed}"
        )
    return observed


def inventory_source_files(
    source_dir: Path, *, source_revision: str = PINNED_IIP_REVISION
) -> tuple[tuple[Path, ...], dict[str, str]]:
    """Enumerate source files with narrowly audited exclusions.

    A broad filename-substring test is forbidden: e.g. contest0001.xml
    is a real conversion candidate, not an intentional test fixture.
    """
    if not source_dir.is_dir():
        raise ValueError(f"source directory does not exist: {source_dir}")
    paths = sorted(path for path in source_dir.glob("*.xml") if path.is_file())
    included: list[Path] = []
    excluded: dict[str, str] = {}
    for path in paths:
        reason = (
            _PINNED_EXCLUSIONS.get(path.name)
            if source_revision == PINNED_IIP_REVISION
            else None
        )
        if reason is not None:
            excluded[path.name] = reason
        else:
            included.append(path)
    if not included:
        raise ValueError(f"no conversion candidates in source directory: {source_dir}")
    return tuple(included), excluded


def require_empty_output_directory(path: Path) -> None:
    """Use only fresh build outputs; never recursively delete caller data."""
    if path.is_symlink():
        raise ValueError(f"output directory must not be a symlink: {path}")
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise ValueError(f"output directory is not empty: {path}")
    else:
        path.mkdir(parents=True, exist_ok=False)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def tf_feature_hashes(directory: Path) -> dict[str, str]:
    """Hash all native .tf features, ignoring disposable Text-Fabric caches."""
    if not directory.is_dir():
        raise ReproducibilityError(f"missing TF feature directory: {directory}")
    features = sorted(
        (path for path in directory.glob("*.tf") if path.is_file()),
        key=lambda path: path.name,
    )
    if not features:
        raise ReproducibilityError(f"no TF feature files in {directory}")
    return {path.name: _file_sha256(path) for path in features}


def compare_tf_feature_hashes(left: Path, right: Path) -> dict[str, str]:
    """Reject missing, extra, and changed .tf files between fresh builds."""
    expected = tf_feature_hashes(left)
    observed = tf_feature_hashes(right)
    if expected != observed:
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        different = sorted(
            name
            for name in set(expected) & set(observed)
            if expected[name] != observed[name]
        )
        raise ReproducibilityError(
            f"TF byte reproducibility failure: missing={missing}, "
            f"extra={extra}, different={different}"
        )
    return expected


def _atomic_write_text(destination: Path, content: str) -> None:
    """Replace one report file atomically, leaving prior bytes intact on I/O failure."""
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def write_build_reports(
    output_dir: Path, report: Mapping[str, object]
) -> tuple[Path, Path]:
    """Persist deterministic JSON and researcher-readable Markdown build artifacts.

    Reports describe an independently validated conversion; they are not
    loaded by Text-Fabric and cannot substitute for TF-native semantics.
    """
    source_files = report.get("source_files")
    if not isinstance(source_files, dict):
        raise ValueError("build report requires source_files accounting")
    converted = source_files.get("converted")
    excluded = source_files.get("excluded")
    failed = source_files.get("failed")
    if not isinstance(converted, list) or not isinstance(excluded, dict):
        raise ValueError("build report requires converted and excluded source files")
    if not isinstance(failed, list):
        raise ValueError("build report requires failed source files")
    if report.get("status") == "success" and failed:
        raise ValueError("cannot report success with failed records")
    if report.get("status") not in {"success", "failed"}:
        raise ValueError("build report requires explicit success/failed status")

    lines = [
        "# IIP-TF conversion and reproducibility report",
        "",
        f"Status: {report['status']}",
        f"Source revision: `{report.get('source_revision', 'unknown')}`",
        f"Converter commit: `{report.get('converter_commit', 'unknown')}`",
        "",
        "## Source-file accounting",
        "",
        f"Converted: {len(converted)}",
        f"Excluded: {len(excluded)}",
        f"Failed: {len(failed)}",
        "",
    ]
    for filename, reason in sorted(excluded.items()):
        lines.append(f"- Excluded `{filename}`: {reason}")
    if report["status"] == "failed":
        parsed = source_files.get("parsed", [])
        unprocessed = source_files.get("unprocessed", [])
        if isinstance(parsed, list) and isinstance(unprocessed, list):
            lines.append(f"Parsed (not necessarily converted): {len(parsed)}")
            lines.append(f"Unprocessed: {len(unprocessed)}")
    for entry in failed:
        if isinstance(entry, dict):
            lines.append(
                f"- Failed: {entry.get('filename')} at {entry.get('stage')}"
                f" ({entry.get('error_type')})"
            )
        else:
            lines.append(f"- Failed: {entry}")
    lines.extend(["", "## Canonical corpus statistics", ""])
    for name in ("signs", "nodes", "edges", "points"):
        if name in report:
            lines.append(f"- {name}: {report[name]}")
    for heading, field in (
        ("Node counts", "node_counts"),
        ("Slot languages", "slot_languages"),
        ("Slot kinds", "slot_kinds"),
        ("TF feature SHA-256 digests", "tf_feature_hashes"),
    ):
        value = report.get(field)
        if not isinstance(value, dict):
            continue
        lines.extend(["", f"## {heading}", ""])
        for key, count in sorted(value.items()):
            lines.append(f"- `{key}`: {count}")
    lines.append("")

    output_dir.mkdir(parents=True, exist_ok=True)
    machine = output_dir / "iip-corpus-report.json"
    readable = output_dir / "iip-corpus-report.md"
    _atomic_write_text(
        machine, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    _atomic_write_text(readable, "\n".join(lines))
    return machine, readable


def validate_oslots_mapping(
    entries: Iterable[tuple[int, Iterable[int]]],
    *,
    sign_count: int,
    node_count: int,
) -> int:
    """Require all TF non-slot nodes to have valid nonempty slot domains."""
    if sign_count < 1 or node_count < 1:
        raise ReproducibilityError("invalid slot/non-slot cardinalities")
    seen: set[int] = set()
    maximum = sign_count + node_count
    for node, slots in entries:
        if node <= sign_count or node > maximum:
            raise ReproducibilityError(f"invalid non-slot oslots source {node}")
        if node in seen:
            raise ReproducibilityError(f"duplicate oslots source {node}")
        seen.add(node)
        has_slot = False
        for slot in slots:
            has_slot = True
            if slot < 1 or slot > sign_count:
                raise ReproducibilityError(
                    f"node {node} has invalid slot target {slot}"
                )
        if not has_slot:
            raise ReproducibilityError(f"node {node} has empty oslots")
    if len(seen) != node_count:
        raise ReproducibilityError(
            f"missing oslots owners: {node_count - len(seen)} "
            "non-slot nodes have no slot domain"
        )
    return len(seen)
