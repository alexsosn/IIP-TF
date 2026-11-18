"""#10: public researcher archive must be accepted *after* an independent download.

These are contract guards for release automation, not a substitute for the
actual GitHub Actions deployment and independent-runner E2E smoke.
"""
from __future__ import annotations

from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github/workflows/publish-researcher-corpus.yml"
)


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_publication_is_an_explicit_main_only_one_shot() -> None:
    workflow = _workflow()
    assert "workflow_dispatch:" in workflow
    assert "branches: [main]" in workflow
    assert '      - ".github/workflows/publish-researcher-corpus.yml"' in workflow
    assert "pull_request:" not in workflow
    assert "workflow_run:" not in workflow
    assert "corpus-data-0.1.0rc1" in workflow
    assert "--prerelease" in workflow
    assert "--target \"$GITHUB_SHA\"" in workflow


def test_pinned_source_and_audited_native_build_are_used() -> None:
    workflow = _workflow()
    assert "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5" in workflow
    for mandatory in (
        "scripts/validate_pinned_tf.py",
        "scripts/validate_pinned_app.py",
        "scripts/build_researcher_archive.py",
        "scripts/smoke_researcher_archive.py",
        "iip-corpus-report.json",
        "iip-tf-corpus.tar.gz",
    ):
        assert mandatory in workflow
    assert "--converter-commit \"$GITHUB_SHA\"" in workflow


def test_only_publisher_can_write_and_cannot_overwrite_a_release() -> None:
    workflow = _workflow()
    assert "  build:" in workflow
    assert "  publish:" in workflow
    assert "  verify_public:" in workflow
    assert "contents: write" in workflow
    assert workflow.count("contents: write") == 1
    assert "gh release create" in workflow
    assert "ref/tags/" in workflow
    assert "sha256sum" in workflow


def test_independent_unauthenticated_download_retests_extracted_tf() -> None:
    workflow = _workflow()
    assert "needs: publish" in workflow
    assert "releases/download/" in workflow
    assert "curl --fail" in workflow
    assert "sha256sum -c" in workflow
    assert "python -m venv" in workflow
    assert "text-fabric>=13.1,<14" in workflow
    assert "scripts/smoke_researcher_archive.py" in workflow
    # No GitHub-provided release asset credentials must be needed at download.
    verify = workflow.split("  verify_public:", maxsplit=1)[1]
    assert "GH_TOKEN:" not in verify
    assert "GITHUB_TOKEN:" not in verify


def test_existing_full_pinned_pr_gate_covers_publication_changes() -> None:
    full_gate = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/validate-pinned-tf.yml"
    ).read_text(encoding="utf-8")
    for path in (
        ".github/workflows/publish-researcher-corpus.yml",
        "tests/test_corpus_publication.py",
    ):
        # PR and main-branch path filters both need the release gate.
        assert full_gate.count(f'      - "{path}"') == 2
