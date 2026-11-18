"""Issue #10: RED-first acceptance for a source-free, offline researcher archive."""
from __future__ import annotations

import hashlib
import json
import tarfile
from importlib import import_module
from pathlib import Path

import pytest

from iip_tf.release_gate import tf_feature_hashes
from iip_tf.source_repair import PINNED_IIP_REVISION

# Import at runtime so the RED suite reaches pytest, not MyPy import discovery.
build_researcher_archive = import_module(
    "scripts.build_researcher_archive"
).build_researcher_archive


@pytest.fixture
def source_build(tmp_path: Path) -> tuple[Path, Path]:
    tf_dir = tmp_path / "native"
    tf_dir.mkdir()
    for name, value in (
        ("otype.tf", b"@node\n@valueType=str\n\n1\tsign\n"),
        ("oslots.tf", b"@edge\n@valueType=str\n\n2\t1\n"),
        ("otext.tf", b"@config\n@sectionTypes=inscription\n"),
        ("glyph.tf", b"@node\n@valueType=str\n\n1\tA\n"),
    ):
        (tf_dir / name).write_bytes(value)
    report = {
        "status": "success",
        "source_revision": PINNED_IIP_REVISION,
        "converter_commit": "a" * 40,
        "source_files": {
            "converted": [f"iip{i:04}.xml" for i in range(5535)],
            "excluded": {"aaTestFile.xml": "pinned source test fixture"},
            "failed": [],
        },
        "tf_feature_hashes": tf_feature_hashes(tf_dir),
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return tf_dir, report_path


def test_archive_is_self_contained_and_excludes_xml_and_conversion_package(
    source_build: tuple[Path, Path], tmp_path: Path,
) -> None:
    tf_dir, report = source_build
    archive = build_researcher_archive(tf_dir, report, tmp_path / "research-corpus.tar.gz")
    assert archive.exists()
    with tarfile.open(archive, mode="r:gz") as stream:
        names = sorted(stream.getnames())
        assert names == [
            "LICENSE",
            "LICENSE_SCOPE.md",
            "START_HERE.txt",
            "app/app.py",
            "app/config.yaml",
            "app/static/display.css",
            "tf/glyph.tf",
            "tf/oslots.tf",
            "tf/otext.tf",
            "tf/otype.tf",
        ]
        for member in stream:
            assert member.isfile()
            assert member.mtime == member.uid == member.gid == 0
            assert member.name.endswith(".xml") is False
        instructions = stream.extractfile("START_HERE.txt")
        assert instructions is not None
        content = instructions.read().decode("utf-8")
        assert "text-fabric" in content
        assert "tf.browser.start" in content
        assert "10.26300/pz1d-st89" in content
        assert "CC BY-NC 4.0" in content
        assert PINNED_IIP_REVISION in content
    # Real TF bytes survive the move; none require an XML or report sidecar.
    with tarfile.open(archive, mode="r:gz") as stream:
        for name in tf_feature_hashes(tf_dir):
            data = stream.extractfile(f"tf/{name}")
            assert data is not None
            assert hashlib.sha256(data.read()).hexdigest() == tf_feature_hashes(tf_dir)[name]


def test_repeatable_archive_bytes(
    source_build: tuple[Path, Path], tmp_path: Path,
) -> None:
    tf_dir, report = source_build
    left = build_researcher_archive(tf_dir, report, tmp_path / "left.tar.gz")
    right = build_researcher_archive(tf_dir, report, tmp_path / "right.tar.gz")
    assert left.read_bytes() == right.read_bytes()


@pytest.mark.parametrize(
    "mutate",
    ["failed", "status", "source", "count", "converter", "hash", "missing_hash"],
)
def test_incomplete_or_unverified_build_never_produces_archive(
    source_build: tuple[Path, Path], tmp_path: Path, mutate: str,
) -> None:
    tf_dir, report_path = source_build
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if mutate == "failed":
        report["source_files"]["failed"] = [{"file": "lost.xml"}]
    elif mutate == "status":
        report["status"] = "failed"
    elif mutate == "source":
        report["source_revision"] = "unverified"
    elif mutate == "count":
        report["source_files"]["converted"].pop()
    elif mutate == "converter":
        report["converter_commit"] = ""
    elif mutate == "hash":
        report["tf_feature_hashes"]["glyph.tf"] = "0" * 64
    elif mutate == "missing_hash":
        del report["tf_feature_hashes"]["glyph.tf"]
    report_path.write_text(json.dumps(report), encoding="utf-8")
    destination = tmp_path / "candidate.tar.gz"
    with pytest.raises(ValueError):
        build_researcher_archive(tf_dir, report_path, destination)
    assert not destination.exists()


def test_modified_or_missing_tf_feature_is_blocking(
    source_build: tuple[Path, Path], tmp_path: Path,
) -> None:
    tf_dir, report = source_build
    (tf_dir / "glyph.tf").write_bytes(b"changed")
    with pytest.raises(ValueError):
        build_researcher_archive(tf_dir, report, tmp_path / "bad.tar.gz")
    (tf_dir / "oslots.tf").unlink()
    with pytest.raises(ValueError):
        build_researcher_archive(tf_dir, report, tmp_path / "missing.tar.gz")


def test_reject_symlinks_instead_of_shipping_external_content(
    source_build: tuple[Path, Path], tmp_path: Path,
) -> None:
    tf_dir, report = source_build
    original = tf_dir / "glyph.tf"
    moved = tmp_path / "external.tf"
    original.rename(moved)
    original.symlink_to(moved)
    with pytest.raises(ValueError, match="symlink"):
        build_researcher_archive(tf_dir, report, tmp_path / "bad.tar.gz")


def test_never_overwrite_existing_user_file(
    source_build: tuple[Path, Path], tmp_path: Path,
) -> None:
    tf_dir, report = source_build
    destination = tmp_path / "notes.tar.gz"
    destination.write_bytes(b"my original research")
    with pytest.raises(FileExistsError):
        build_researcher_archive(tf_dir, report, destination)
    assert destination.read_bytes() == b"my original research"


def test_racing_exclusive_open_never_deletes_another_writers_file(
    source_build: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The preflight absence check and exclusive creation are not atomic."""
    tf_dir, report = source_build
    destination = tmp_path / "racing-researcher-archive.tar.gz"
    original_open = Path.open

    def simulate_other_writer(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> object:
        if path == destination and mode == "xb":
            destination.write_bytes(b"other researcher's valuable content")
            raise FileExistsError("another writer won the exclusive-open race")
        return original_open(path, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, "open", simulate_other_writer)
    with pytest.raises(FileExistsError, match="another writer"):
        build_researcher_archive(tf_dir, report, destination)
    assert destination.read_bytes() == b"other researcher's valuable content"
