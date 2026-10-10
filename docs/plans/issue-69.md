# Issue #69 — fast, fail-closed pinned workflow preflight

Research: `.github/workflows/ci.yml` currently runs Ruff, strict MyPy, pytest
in one job. `.github/workflows/validate-pinned-tf.yml` immediately fetches
Brown XML and rebuilds the full 5,535-inscription corpus twice before its
browser smoke. During PR #68 several work-in-progress heads were proven
broken by ordinary CI, yet expensive pinned jobs had already consumed runner
time and were canceled after the subsequent fix.

Plan/requirements:
1. RED static workflow tests demonstrate the desired contract absent on main:
   a separate fast preflight, full Ruff/MyPy/pytest test gate, full pinned
   validate job dependent on that gate, and an **explicit failed validate
   status** on a failed prerequisite instead of silently skipping a potentially
   required job.
2. GREEN: preflight checks out the **exact event head**, installs standard
   dev dependencies, runs Ruff, MyPy and all pytest in that order. The
   expensive validate job depends on preflight and uses `if: always()` so it
   always starts when the workflow is scheduled, but runs a FIRST step
   checking `needs.preflight.result` before checkout, Brown download, or
   full conversion. If preflight was unsuccessful, this step emits an
   explanatory GitHub error and exits nonzero. The rest is untouched.
3. Use the existing pip cache; this duplicates an install vs standalone CI
   but avoids two TF builds for broken changes. No cross-workflow
   `workflow_run` trust or matching-SHA race; no dependency on a
   potentially missing path-filtered CI run.
4. Test the real Actions RED/green job statuses, full pinned success on
   a verified head, and independent skeptical review. Preserve fast CI,
   entire pinned release gate, and artifact upload semantics.
5. Prefer measuring timing and job savings from real runs before more
   architecture/optimization changes. No semantic corpus modifications.

Risk: job `if: always()` may still schedule an inexpensive validate job
when preflight is red; intentional, because a skipped required GitHub job
could be treated as green. Workflow cancellation obeys existing PR
concurrency, and should cancel both jobs together. Test its actual behavior.
