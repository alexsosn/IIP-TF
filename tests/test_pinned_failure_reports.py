"""Fail-closed conversion-failure reports: TDD regression for issue #60."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from iip_tf import release_gate
from iip_tf.source_repair import PINNED_IIP_REVISION
from scripts import validate_pinned_tf as pinned


def _source_tree(_source: Path, *, expected_sha: str) -> str:
    assert expected_sha
    return "verified-fixture-tree"


def _empty_ir(path: Path, *, source_revision: str) -> Any:
    assert source_revision
    assert path.exists()
    return SimpleNamespace(signs=(), nodes=(), edges=())


def test_parse_failure_persists_exact_file_stage_and_unprocessed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    for name in (
        "aaTestFile.xml", "aaa-good.xml", "mmm-bad.xml", "zzz-not-parsed.xml"
    ):
        (source_dir / name).write_text("<TEI/>", encoding="utf-8")

    monkeypatch.setattr(pinned, "require_source_tree_sha", _source_tree)
    monkeypatch.setattr(pinned, "EXPECTED_PARSED", 3)

    def parse(path: Path, *, source_revision: str) -> Any:
        if path.name == "mmm-bad.xml":
            raise ValueError("invalid source: <TEI>sensitive content</TEI>")
        return _empty_ir(path, source_revision=source_revision)

    monkeypatch.setattr(pinned, "parse_epidoc_file", parse)
    output_dir = tmp_path / "native-tf"
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_pinned_tf.py", str(source_dir), str(output_dir),
         "--revision", PINNED_IIP_REVISION, "--converter-commit", "test-sha"],
    )
    with pytest.raises(ValueError, match="invalid source"):
        pinned.main()

    report_file = tmp_path / "native-tf-reports" / "iip-corpus-report.json"
    assert report_file.exists(), "failed conversion must leave a durable report"
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert report["source_files"]["converted"] == []
    assert report["source_files"]["parsed"] == ["aaa-good.xml"]
    assert report["source_files"]["unprocessed"] == ["zzz-not-parsed.xml"]
    assert report["source_files"]["excluded"] == {
        "aaTestFile.xml": "pinned source test fixture"
    }
    assert report["source_files"]["failed"] == [
        {"filename": "mmm-bad.xml", "stage": "parse", "error_type": "ValueError"}
    ]
    assert report["verified_source_tree_git_sha1"] == "verified-fixture-tree"
    assert "<TEI>" not in report_file.read_text(encoding="utf-8")
    assert "Status: failed" in (
        tmp_path / "native-tf-reports" / "iip-corpus-report.md"
    ).read_text(encoding="utf-8")


def test_tf_write_failure_reports_no_converted_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "aaTestFile.xml").write_text("<TEI/>", encoding="utf-8")
    (source_dir / "good.xml").write_text("<TEI/>", encoding="utf-8")
    monkeypatch.setattr(pinned, "require_source_tree_sha", _source_tree)
    monkeypatch.setattr(pinned, "EXPECTED_PARSED", 1)
    for key in (
        "EXPECTED_SIGNS", "EXPECTED_NODES", "EXPECTED_EDGES",
        "EXPECTED_POINTS", "EXPECTED_EMPTY_STRUCTURAL", "EXPECTED_SEGMENTED_TOKEN_IDENTITIES"
    ):
        monkeypatch.setattr(pinned, key, 0)
    monkeypatch.setattr(pinned, "parse_epidoc_file", _empty_ir)

    def fail_write(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("simulated disk full")

    monkeypatch.setattr(pinned, "write_tf_corpus", fail_write)
    monkeypatch.setattr(
        sys, "argv",
        ["validate_pinned_tf.py", str(source_dir), str(tmp_path / "native-tf"),
         "--revision", PINNED_IIP_REVISION, "--converter-commit", "test-sha"],
    )
    with pytest.raises(OSError, match="disk full"):
        pinned.main()

    report_file = tmp_path / "native-tf-reports" / "iip-corpus-report.json"
    assert report_file.exists()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert report["source_files"]["converted"] == []
    assert report["source_files"]["parsed"] == ["good.xml"]
    assert report["source_files"]["unprocessed"] == []
    assert report["source_files"]["failed"] == [
        {"filename": None, "stage": "tf_write", "error_type": "OSError"}
    ]


def test_atomic_report_replace_keeps_prior_bytes_when_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior: dict[str, object] = {
        "status": "success",
        "source_files": {"converted": ["good.xml"], "excluded": {}, "failed": []},
    }
    machine, readable = release_gate.write_build_reports(tmp_path, prior)
    original_json = machine.read_bytes()
    original_markdown = readable.read_bytes()

    failed: dict[str, object] = {
        "status": "failed",
        "source_files": {
            "converted": [],
            "parsed": [],
            "unprocessed": [],
            "excluded": {},
            "failed": [{"filename": "bad.xml", "stage": "parse", "error_type": "ValueError"}],
        },
    }

    def simulated_io_failure(_source: Any, _destination: Any) -> None:
        raise OSError("atomic rename failed")

    with monkeypatch.context() as patch:
        patch.setattr(release_gate.os, "replace", simulated_io_failure)
        with pytest.raises(OSError, match="rename failed"):
            release_gate.write_build_reports(tmp_path, failed)

    assert machine.read_bytes() == original_json
    assert readable.read_bytes() == original_markdown
    assert not tuple(tmp_path.glob(".iip-corpus-report.json.*"))


def test_failure_report_workflow_retains_browser_gate_and_mandatory_success_files() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/validate-pinned-tf.yml").read_text(
        encoding="utf-8"
    )
    assert "Validate native app + Flask browser against pinned corpus" in workflow
    assert "Require successful pinned build report" in workflow
    assert "if: success()" in workflow
    assert "Upload reproducibility or failure reports" in workflow
    assert "if: always()" in workflow
    assert "if-no-files-found: warn" in workflow
