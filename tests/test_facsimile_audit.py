"""Research contract for matching explicit EpiDoc graphic URLs to the image tree."""
from pathlib import Path

import pytest

from iip_tf.facsimile_audit import audit_facsimiles, image_paths_from_tree


def test_facsimile_inventory_uses_explicit_refs_not_inscription_ids(tmp_path: Path) -> None:
    def write(name: str, graphics: str) -> None:
        (tmp_path / name).write_text(
            '<TEI xmlns="http://www.tei-c.org/ns/1.0"><facsimile>'
            f"{graphics}</facsimile></TEI>",
            encoding="utf-8",
        )

    write(
        "jeru0566.xml",
        '<surface><graphic url="jeru0565b.jpg"/><graphic/>'
        '<surface><graphic url=""/></surface></surface>'
        '<graphic url="BS0002.reg.gif"/>'
        '<graphic url="images/jeru0566.jpg"/>'
        '<graphic url="https://example.org/a.jpg"/>'
        '<!-- <graphic url="masa0775.jpg"/> -->',
    )
    write("other.xml", '<graphic url="jeru0565b.jpg"/><graphic url="JERU0566.jpg"/>')
    write("masa0775.xml", '<graphic url=""/>')
    write("aaTestFile.xml", '<graphic url="masa0775.jpg"/>')
    paths = {"jeru0565b.jpg", "jeru0566.jpg", "masa0775.jpg"}

    report = audit_facsimiles(tmp_path, paths)

    assert "source_revision" not in report  # arbitrary fixture is not authenticated
    assert "image_revision" not in report
    assert "image_tree" not in report
    assert report["records"] == 3
    assert report["excluded"] == {"aaTestFile.xml": "pinned source test fixture"}
    assert report["graphic_occurrences"] == 9
    assert report["status_counts"] == {
        "exact": 2, "missing_attribute": 1, "empty": 2,
        "unmatched_filename": 2, "unsupported": 2,
    }
    assert report["records_with_exact"] == 2
    assert report["matched_filenames"] == ["jeru0565b.jpg"]
    assert report["unreferenced_image_paths"] == ["jeru0566.jpg", "masa0775.jpg"]
    assert report["shared_exact_refs"] == {
        "jeru0565b.jpg": ["jeru0566.xml", "other.xml"]
    }
    assert report["unmatched_refs"] == {"BS0002.reg.gif": 1, "JERU0566.jpg": 1}


def test_image_tree_requires_complete_expected_tree_and_regular_root_blobs() -> None:
    tree = {
        "sha": "expected",
        "truncated": False,
        "tree": [{"path": "a.jpg", "type": "blob", "mode": "100644"}],
    }
    assert image_paths_from_tree(tree, expected_sha="expected") == {"a.jpg"}
    # The real Brown image tree contains 58 regular executable-mode JPEGs.
    executable = {**tree, "tree": [{"path": "b.jpg", "type": "blob", "mode": "100755"}]}
    assert image_paths_from_tree(executable, expected_sha="expected") == {"b.jpg"}
    with pytest.raises(ValueError):
        image_paths_from_tree(tree, expected_sha="other")
    with pytest.raises(ValueError):
        image_paths_from_tree({**tree, "truncated": True}, expected_sha="expected")
    with pytest.raises(ValueError):
        image_paths_from_tree(
            {**tree, "tree": [{"path": "a.jpg", "type": "blob", "mode": "120000"}]},
            expected_sha="expected",
        )
