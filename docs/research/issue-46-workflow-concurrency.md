# Issue #46 — GitHub Actions PR concurrency research

Date: 2026-10-10. Baseline: main at f08baafc9d09c1f7556d6c57fea9b4e644a1208e.

## Evidence

During PR #45, every synchronize generated independent CI, pinned textual IR,
and pinned native TF runs. Many superseded full-source jobs remained queued while
the exact current head was awaiting runner capacity.

GitHub Actions workflow-level `concurrency` is repository-wide; groups shared
between different workflows can cancel each other's work. GitHub automatically
replaces older pending runs within a group. `cancel-in-progress: true` also
cancels a running predecessor.

Official reference:
https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency

## Production workflow inventory

The active workflows accepting pull requests are:

- `.github/workflows/ci.yml`
- `.github/workflows/audit-pinned-iip.yml`
- `.github/workflows/validate-pinned-source.yml`
- `.github/workflows/validate-pinned-text-ir.yml`
- `.github/workflows/validate-pinned-tf.yml`

`research-issue34.yml`, `research-issue38.yml`, and
`research-issue43.yml` are dormant, branch-scoped research workflows rather
than general PR gates; do not change their triggers.

## Decision

Add the same top-level policy to each active PR workflow:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event_name }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

- `github.workflow` partitions by workflow.
- `github.event_name` partitions PR and push events.
- PR number is assigned by the base repository, so fork-head branch names
  cannot collide, and two PRs from forks with the same branch name stay separate.
- On push, `github.event.pull_request.number` is undefined, so the unique
  `github.run_id` preserves **all** main validation runs, including pending
  runs. A simple `github.ref` fallback would replace pending main runs even
  with `cancel-in-progress: false`.
- For a PR synchronize, the next run of the **same workflow** uses the same
  group, replacing pending predecessors and canceling a running predecessor.

## Validation strategy

RED: policy test inspects all five active workflows, requires the exact
top-level policy, and simulates collisions across PR numbers, workflow names,
event types, fork branches, and independent main pushes.

GREEN: insert that policy without modifying job steps, path filters,
permissions, source pins, or branch triggers.

Runtime evidence: two successive changes to this PR's CI workflow should show
that the superseded head's CI run is cancelled and the final exact-head run is
green. Other pinned workflows must still trigger on changes to themselves;
their exact-head jobs must succeed.

Adversarial review must challenge scope collisions and ensure push/main
validation has not been weakened.
