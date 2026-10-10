"""Pinned workflow must fail closed before expensive corpus conversion."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github/workflows/validate-pinned-tf.yml"
)


def _jobs() -> tuple[str, str]:
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "\njobs:\n" in content
    jobs = content.split("\njobs:\n", 1)[1]
    assert "\n  preflight:\n" in jobs, "missing fast prerequisite job"
    preflight = jobs.split("\n  preflight:\n", 1)[1].split(
        "\n  validate:\n", 1
    )[0]
    validate = jobs.split("\n  validate:\n", 1)[1]
    return preflight, validate


def test_pinned_full_build_depends_on_all_fast_code_gates() -> None:
    preflight, validate = _jobs()
    for check in (
        "Checkout exact event head",
        "Install",
        "ruff check .",
        "mypy",
        "pytest -q",
    ):
        assert check in preflight
    assert "Build and reload complete native TF corpus" not in preflight
    assert "needs: preflight" in validate
    assert "if: always()" in validate


def test_pinned_dependency_failure_fails_required_job_before_network_or_build() -> None:
    _, validate = _jobs()
    check = validate.index("Require green preflight")
    source = validate.index("Fetch pinned Brown IIP source")
    build = validate.index("Build and reload complete native TF corpus")
    assert check < source < build
    assert "needs.preflight.result" in validate
    assert '!= "success"' in validate
    assert "exit 1" in validate
    assert "Checkout exact event head" in validate
    assert "github.event.pull_request.head.sha || github.sha" in validate
    assert "Require successful pinned build report" in validate
    assert "Upload reproducibility or failure reports" in validate
