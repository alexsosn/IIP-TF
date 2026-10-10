"""Issue #72: fail-closed small real-IIP preflight before full corpus build."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_pinned_canary.py"
MANIFEST = ROOT / "schema/pinned-canary-blobs.tsv"
WORKFLOW = ROOT / ".github/workflows/validate-pinned-tf.yml"
EXPECTED = {
    "abil0001.xml", "bshe0146.xml", "caes0260.xml",
    "chor0001.xml", "haif0003.xml", "masa0286.xml",
}


def canary() -> ModuleType:
    spec = importlib.util.spec_from_file_location("iip_pinned_canary", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canary_manifest_pins_exact_six_upstream_git_blobs() -> None:
    assert MANIFEST.is_file()
    app = canary()
    values = app.read_manifest(MANIFEST)
    assert set(values) == EXPECTED
    assert len(set(values.values())) == len(values)
    assert all(len(digest) == 40 for digest in values.values())
    assert values["bshe0146.xml"] == "08370d675b64cfecaa7d433f825d4f1be9d2db8e"


def test_git_blob_hash_matches_git_object_header() -> None:
    app = canary()
    sample = b"<TEI>source</TEI>\n"
    expected = hashlib.sha1(
        b"blob " + str(len(sample)).encode() + b"\x00" + sample,
        usedforsecurity=False,
    ).hexdigest()
    assert app.git_blob_sha(sample) == expected
    with pytest.raises(ValueError, match="blob"):
        app.verify_blob("bshe0146.xml", b"tampered", "0" * 40)


def test_download_refuses_tampered_bytes_before_writing(tmp_path: Path) -> None:
    app = canary()
    source = b"<TEI/>"
    digest = app.git_blob_sha(source)
    fetched: list[str] = []

    def fetch(url: str) -> bytes:
        fetched.append(url)
        return source + b"tampered"

    with pytest.raises(ValueError, match="blob"):
        app.download_verified({"bshe0146.xml": digest}, tmp_path, fetch)
    assert not (tmp_path / "bshe0146.xml").exists()
    assert len(fetched) == 1
    assert "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5" in fetched[0]
    assert fetched[0].endswith("/epidoc-files/bshe0146.xml")


def test_manifest_blocks_duplicate_path_traversal_and_mutable_refs(tmp_path: Path) -> None:
    app = canary()
    good = MANIFEST.read_text(encoding="utf-8")
    for content in (
        good + "\nbshe0146.xml\t" + ("0" * 40),
        good.replace("bshe0146.xml", "../bad.xml", 1),
        good.replace("08370d675b64cfecaa7d433f825d4f1be9d2db8e", "main", 1),
    ):
        path = tmp_path / "manifest.tsv"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            app.read_manifest(path)


def test_preflight_real_source_canary_before_any_full_brown_download() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "python scripts/validate_pinned_canary.py" in workflow
    assert "scripts/validate_pinned_canary.py" in workflow
    assert "schema/pinned-canary-blobs.tsv" in workflow
    preflight = workflow.split("  preflight:\n", 1)[1].split("  validate:\n", 1)[0]
    validate = workflow.split("  validate:\n", 1)[1]
    assert preflight.index("name: Pytest") < preflight.index(
        "name: Authenticated real-IIP canary"
    )
    assert "Fetch pinned Brown IIP source" not in preflight
    assert "Build and reload complete native TF corpus" not in preflight
    assert "needs: preflight" in validate
    assert "Require green preflight" in validate
    assert "Fetch pinned Brown IIP source" in validate
    assert "Build and reload complete native TF corpus" in validate
