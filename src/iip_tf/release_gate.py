"""Release-gate primitives: exact source accounting and TF byte reproducibility.

Reports and SHA manifests are build artifacts, never semantic sidecars.
"""
from __future__ import annotations

import hashlib
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
