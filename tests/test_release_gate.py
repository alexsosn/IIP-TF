"""RED acceptance tests for issue #7: source accounting and deterministic TF."""
from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.release_gate import (
    ReproducibilityError,
    compare_tf_feature_hashes,
    inventory_source_files,
    tf_feature_hashes,
)


def test_source_inventory_excludes_only_pinned_source_test_file(tmp_path: Path) -> None:
    for name in ("aaTestFile.xml", "contest0001.xml", "iiptest0001.xml", "abil0001.xml"):
        (tmp_path / name).write_text("<TEI/>", encoding="utf-8")

    files, excluded = inventory_source_files(tmp_path)
    assert [path.name for path in files] == [
        "abil0001.xml", "contest0001.xml", "iiptest0001.xml"
    ]
    assert excluded == {"aaTestFile.xml": "pinned source test fixture"}


def test_source_inventory_rejects_missing_and_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source directory"):
        inventory_source_files(tmp_path / "missing")
    with pytest.raises(ValueError, match="no conversion candidates"):
        inventory_source_files(tmp_path)
    (tmp_path / "aaTestFile.xml").write_text("<TEI/>", encoding="utf-8")
    with pytest.raises(ValueError, match="no conversion candidates"):
        inventory_source_files(tmp_path)


def test_tf_hashes_are_bytewise_stable_and_ignore_cache_files(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    for directory in (first, second):
        (directory / "otype.tf").write_bytes(b"\xe2\x82\xac\n")
        (directory / "oslots.tf").write_bytes(b"1\t2\n")
    (second / ".tf").mkdir()
    (second / ".tf" / "otype.tfx").write_bytes(b"cache differs")

    manifest = compare_tf_feature_hashes(first, second)
    assert manifest == tf_feature_hashes(first)
    assert set(manifest) == {"otype.tf", "oslots.tf"}
    assert all(len(value) == 64 for value in manifest.values())


@pytest.mark.parametrize("change", ["changed", "missing", "extra"])
def test_tf_hash_comparison_fails_closed(
    tmp_path: Path, change: str
) -> None:
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "otype.tf").write_bytes(b"same")
    (right / "otype.tf").write_bytes(b"same")
    if change == "changed":
        (right / "otype.tf").write_bytes(b"different")
    elif change == "missing":
        (right / "otype.tf").unlink()
    else:
        (right / "other.tf").write_bytes(b"extra")
    with pytest.raises(ReproducibilityError):
        compare_tf_feature_hashes(left, right)


def test_tf_hash_comparison_rejects_empty_feature_directory(tmp_path: Path) -> None:
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    with pytest.raises(ReproducibilityError, match="no TF feature"):
        compare_tf_feature_hashes(left, right)
