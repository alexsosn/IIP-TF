"""Regression tests for #46 workflow-level PR concurrency boundaries."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

ACTIVE_PR_WORKFLOWS = {
    "ci.yml",
    "audit-pinned-iip.yml",
    "validate-pinned-source.yml",
    "validate-pinned-text-ir.yml",
    "validate-pinned-tf.yml",
}

GROUP = (
    "  group: ${{ github.workflow }}-${{ github.event_name }}"
    "-${{ github.event.pull_request.number || github.run_id }}"
)
CANCEL = "  cancel-in-progress: ${{ github.event_name == 'pull_request' }}"


def test_all_active_pr_workflows_have_scoped_concurrency_policy() -> None:
    seen: set[str] = set()
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "\n  pull_request:" not in text:
            continue
        seen.add(path.name)
        assert "\nconcurrency:\n" in text, path.name
        header, jobs = text.split("\njobs:\n", 1)
        assert jobs
        assert header.count("\nconcurrency:\n") == 1, path.name
        assert GROUP in header, path.name
        assert CANCEL in header, path.name
        assert header.count("\n  group: ") == 1, path.name
        assert header.count("\n  cancel-in-progress: ") == 1, path.name

    assert seen == ACTIVE_PR_WORKFLOWS


def _group(workflow: str, event: str, *, pr_number: int | None, run_id: int) -> str:
    """Model the reviewed Actions expression for representative events."""
    value = pr_number or run_id
    return f"{workflow}-{event}-{value}"


def test_groups_isolate_workflows_prs_forks_and_main_runs() -> None:
    ci_pr7 = _group("CI", "pull_request", pr_number=7, run_id=101)
    ci_pr7_new_head = _group("CI", "pull_request", pr_number=7, run_id=102)
    ci_pr8_same_fork_branch = _group("CI", "pull_request", pr_number=8, run_id=103)
    pinned_pr7 = _group("Validate pinned native TF", "pull_request", pr_number=7, run_id=104)
    ci_main1 = _group("CI", "push", pr_number=None, run_id=105)
    ci_main2 = _group("CI", "push", pr_number=None, run_id=106)

    assert ci_pr7 == ci_pr7_new_head
    assert len({ci_pr7, ci_pr8_same_fork_branch, pinned_pr7, ci_main1, ci_main2}) == 5
    assert ci_main1 != ci_main2


def test_only_pr_runs_cancel_in_progress() -> None:
    assert "github.event_name == 'pull_request'" in CANCEL
    assert "github.run_id" in GROUP
    assert "github.event.pull_request.number" in GROUP
    assert "github.workflow" in GROUP
