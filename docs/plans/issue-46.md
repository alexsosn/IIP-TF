# Issue #46 — research → plan → RED/GREEN → test → independent review

1. Audit the five production workflows and the official Actions concurrency
   behavior; leave dormant research workflows unchanged.
2. Add a RED regression test that requires top-level per-workflow/per-PR
   concurrency and preserves main push runs through unique run IDs.
3. Add the identical concurrency stanza in each active PR workflow.
4. Validate syntax and expected group disjointness, run Ruff, strict MyPy and
   pytest, then observe actual GitHub Actions cancellation for an older PR
   synchronize head.
5. Independently review the *exact final head* for fork collisions, missing
   workflow coverage, main-run starvation/cancellation, and accidental changes
   to triggers or source gates.
6. Merge only after final-head CI and all triggered pinned gates pass.

No changes to conversion semantics or source corpus are in scope.
