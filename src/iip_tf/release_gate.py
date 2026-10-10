"""Release-gate primitives: exact source accounting and TF byte reproducibility.

Reports and SHA manifests are build artifacts, never semantic sidecars.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

_PINNED_EXCLUSIONS = {"aaTestFile.xml": "pinned source test fixture"}


class ReproducibilityError(ValueError):
    """A TF corpus feature set is missing or differs byte-for-byte."""


def inventory_source_files(source_dir: Path) -> tuple[tuple[Path, ...], dict[str, str]]:
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
        reason = _PINNED_EXCLUSIONS.get(path.name)
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
    for entry in failed:
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
    machine.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readable.write_text("\n".join(lines), encoding="utf-8")
    return machine, readable
