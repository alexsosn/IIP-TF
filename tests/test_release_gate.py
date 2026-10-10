"""RED acceptance tests for issue #7: source accounting and deterministic TF."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from iip_tf.release_gate import (
    ReproducibilityError,
    compare_tf_feature_hashes,
    git_source_tree_sha,
    inventory_source_files,
    require_empty_output_directory,
    require_source_tree_sha,
    tf_feature_hashes,
    validate_oslots_mapping,
    write_build_reports,
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


def test_reproducibility_report_is_human_readable_and_machine_complete(
    tmp_path: Path,
) -> None:
    report: dict[str, object] = {
        "source_revision": "pinned-upstream-sha",
        "converter_commit": "exact-converter-sha",
        "status": "success",
        "source_files": {
            "converted": ["abil0001.xml", "contest0001.xml"],
            "excluded": {"aaTestFile.xml": "pinned source test fixture"},
            "failed": [],
        },
        "signs": 12,
        "nodes": 5,
        "edges": 9,
        "node_counts": {"inscription": 2},
        "slot_languages": {"grc": 10, "he": 2},
        "slot_kinds": {"visible": 11, "anchor": 1},
        "tf_feature_hashes": {"otype.tf": "a" * 64},
    }
    machine, readable = write_build_reports(tmp_path, report)
    assert machine.parent == readable.parent == tmp_path
    assert json.loads(machine.read_text(encoding="utf-8")) == report
    assert readable.suffix == ".md"
    text = readable.read_text(encoding="utf-8")
    for expected in (
        "pinned-upstream-sha", "exact-converter-sha",
        "aaTestFile.xml", "pinned source test fixture",
        "Converted: 2", "Excluded: 1", "Failed: 0",
        "otype.tf", "grc", "anchor",
    ):
        assert expected in text


def test_failed_build_cannot_be_reported_as_success(tmp_path: Path) -> None:
    report: dict[str, object] = {
        "status": "success",
        "source_files": {
            "converted": ["abil0001.xml"],
            "excluded": {},
            "failed": [{"path": "invalid.xml", "error": "invalid TEI"}],
        },
    }
    with pytest.raises(ValueError, match="failed records"):
        write_build_reports(tmp_path, report)
    assert not list(tmp_path.glob("*.json"))


def test_output_guard_preserves_existing_user_files(tmp_path: Path) -> None:
    output = tmp_path / "valuable-output"
    output.mkdir()
    valuable = output / "research-notes.txt"
    valuable.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="not empty"):
        require_empty_output_directory(output)
    assert valuable.read_text(encoding="utf-8") == "keep"


def test_output_guard_creates_new_owned_directory(tmp_path: Path) -> None:
    output = tmp_path / "build" / "pinned-tf"
    require_empty_output_directory(output)
    assert output.is_dir() and not list(output.iterdir())
    require_empty_output_directory(output)


def test_report_directory_guard_preserves_existing_report(
    tmp_path: Path,
) -> None:
    reports = tmp_path / "pinned-tf-reports"
    reports.mkdir()
    prior = reports / "iip-corpus-report.md"
    prior.write_text("independent prior build", encoding="utf-8")
    with pytest.raises(ValueError, match="not empty"):
        require_empty_output_directory(reports)
    assert prior.read_text(encoding="utf-8") == "independent prior build"


def test_output_guard_refuses_symlink_directory(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "protect.txt").write_text("do not alter", encoding="utf-8")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        require_empty_output_directory(alias)
    assert (real / "protect.txt").read_text(encoding="utf-8") == "do not alter"

def test_non_pinned_source_revision_does_not_exclude_filename(tmp_path: Path) -> None:
    (tmp_path / "aaTestFile.xml").write_text("<TEI/>", encoding="utf-8")
    files, excluded = inventory_source_files(
        tmp_path, source_revision="different-upstream-revision"
    )
    assert [path.name for path in files] == ["aaTestFile.xml"]
    assert excluded == {}


def test_pinned_revision_exclusion_is_source_specific(tmp_path: Path) -> None:
    from iip_tf.source_repair import PINNED_IIP_REVISION

    for filename in ("aaTestFile.xml", "contest0001.xml"):
        (tmp_path / filename).write_text("<TEI/>", encoding="utf-8")
    files, excluded = inventory_source_files(
        tmp_path, source_revision=PINNED_IIP_REVISION
    )
    assert [path.name for path in files] == ["contest0001.xml"]
    assert excluded == {"aaTestFile.xml": "pinned source test fixture"}


def test_oslots_mapping_checks_all_non_slot_owners() -> None:
    assert validate_oslots_mapping(
        [(4, [1, 2]), (5, [3]), (6, [2, 3])],
        sign_count=3,
        node_count=3,
    ) == 3


@pytest.mark.parametrize(
    "edges, error",
    [
        ([(4, [1]), (5, [2])], "missing"),
        ([(4, [1]), (5, []), (6, [3])], "empty"),
        ([(4, [1]), (5, [4]), (6, [3])], "invalid slot"),
        ([(2, [1]), (5, [2]), (6, [3])], "invalid non-slot"),
        ([(4, [1]), (4, [2]), (5, [3]), (6, [1])], "duplicate"),
        ([(4, [1]), (5, [2]), (7, [3])], "invalid non-slot"),
    ],
)
def test_oslots_mapping_blocks_orphans_and_wrong_feature_domain(
    edges: list[tuple[int, list[int]]], error: str
) -> None:
    with pytest.raises(ReproducibilityError, match=error):
        validate_oslots_mapping(edges, sign_count=3, node_count=3)


def test_git_source_tree_fingerprint_matches_independent_git_write_tree(tmp_path: Path) -> None:
    # Independently generated via git init; git add epidoc-files/; git write-tree;
    # git ls-tree <root_sha> epidoc-files -> d93d77737d2778b65ebb493f153bbbb05120ccbd.
    (tmp_path / "aaTestFile.xml").write_bytes(b"<TEI/>\n")
    (tmp_path / "abil0001.xml").write_bytes(b"<TEI><text>ABC</text></TEI>\n")
    expected = "d93d77737d2778b65ebb493f153bbbb05120ccbd"
    assert git_source_tree_sha(tmp_path) == expected
    assert require_source_tree_sha(tmp_path, expected_sha=expected) == expected


def test_pinned_source_fingerprint_rejects_same_shape_reading_changes(tmp_path: Path) -> None:
    (tmp_path / "aaTestFile.xml").write_bytes(b"<TEI/>\n")
    inscription = tmp_path / "abil0001.xml"
    inscription.write_bytes(b"<TEI><text>ABC</text></TEI>\n")
    expected = git_source_tree_sha(tmp_path)
    inscription.write_bytes(b"<TEI><text>ABD</text></TEI>\n")
    with pytest.raises(ReproducibilityError, match="source tree"):
        require_source_tree_sha(tmp_path, expected_sha=expected)


@pytest.mark.parametrize("change", ["missing", "extra", "symlink", "nested"])
def test_source_tree_fingerprint_fails_closed_on_untracked_paths(
    tmp_path: Path, change: str
) -> None:
    (tmp_path / "aaTestFile.xml").write_bytes(b"<TEI/>\n")
    inscription = tmp_path / "abil0001.xml"
    inscription.write_bytes(b"<TEI><text>ABC</text></TEI>\n")
    expected = git_source_tree_sha(tmp_path)
    if change == "missing":
        inscription.unlink()
    elif change == "extra":
        (tmp_path / "untracked.txt").write_text("unexpected", encoding="utf-8")
    elif change == "symlink":
        inscription.unlink()
        inscription.symlink_to(tmp_path / "aaTestFile.xml")
    else:
        (tmp_path / "nested").mkdir()
    with pytest.raises(ReproducibilityError):
        require_source_tree_sha(tmp_path, expected_sha=expected)
