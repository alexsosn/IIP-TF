"""Researcher-facing public corpus download URL and attribution contract (#10).

Only publish these links after the post-merge anonymous-release verification
passes. The tests protect documentation against future stale candidate wording.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://github.com/alexsosn/IIP-TF/releases/download/corpus-data-0.1.0rc2"


def test_readme_offers_versioned_public_archive_and_preserves_release_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{BASE}/iip-tf-corpus.tar.gz" in readme
    assert "docs/guides/researcher-distribution.md" in readme
    assert "CC BY-NC 4.0" in readme
    assert "0.1.0" in readme
    assert "not yet" in readme.lower() or "not the final" in readme.lower()
    assert "tf alexsosn/IIP-TF" not in readme


def test_researcher_guide_downloads_archive_checksum_and_provenance() -> None:
    guide = (
        ROOT / "docs/guides/researcher-distribution.md"
    ).read_text(encoding="utf-8")
    for asset in (
        "iip-tf-corpus.tar.gz",
        "iip-tf-corpus.tar.gz.sha256",
        "corpus-provenance.json",
    ):
        assert f"{BASE}/{asset}" in guide
    assert "sha256sum -c iip-tf-corpus.tar.gz.sha256" in guide
    assert "CC BY-NC 4.0" in guide
    assert "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5" in guide
    assert "python -m tf.browser.start" in guide
    assert "text-fabric>=13.1,<14" in guide
    assert "app.webLink(inscription, urlOnly=True)" in guide
    assert "Original EpiDoc" in guide
    assert "no official IIP-TF 0.1.0" in guide.lower() or "0.1.0 has not" in guide.lower()


def test_quickstart_distinguishes_public_data_from_converter_source_build() -> None:
    guide = (ROOT / "docs/guides/researcher-quickstart.md").read_text(encoding="utf-8")
    intro, source_build = guide.split("## 1. Build the authenticated corpus", 1)
    assert "corpus-data-0.1.0rc2" in intro
    assert "Final IIP-TF 0.1.0 has not been released" in intro
    assert "[standalone download and installation guide](researcher-distribution.md)" in intro
    assert "without cloning the converter" in intro
    assert "No released auto-downloadable" not in guide
    assert "Build the authenticated corpus" in source_build
    assert "from iip_tf.researcher_queries import" in source_build
