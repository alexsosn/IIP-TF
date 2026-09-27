# Autonomous development loop

This is the default execution loop for coding agents working on IIP-TF.

## 1. Select and claim work

- Prefer the earliest actionable dependency of release gate #12.
- Read the issue, linked research/design, open PRs, and recent related issues.
- Do not start a duplicate implementation.
- State the issue number in the branch/PR.

## 2. Research

Inspect actual current source/code/contracts.

For corpus-semantic work, research must answer:

- what EpiDoc constructs actually occur;
- how often and in which combinations;
- whether the construct is textual, editorial, structural, metadata, or provenance;
- what existing IIP processing does with it;
- what Text-Fabric invariants constrain the representation;
- whether an ETCBC/DSS/BHSA convention genuinely matches the semantics.

Record durable findings in `research.md` or a focused `docs/research/` artifact.

## 3. Plan

Write acceptance criteria and the smallest implementation that preserves source meaning. Architectural changes require an ADR or explicit update to `design.md`.

## 4. RED-first TDD

For behavior changes:

1. add a deterministic failing test against the production API/path;
2. run it and preserve the observed failure in the PR description or development record;
3. implement the smallest correct fix;
4. run the focused test to GREEN;
5. run the affected suite.

Fixtures should be minimal but must be grounded in measured upstream constructs.

## 5. Integration/full-corpus gates

Run risk-appropriate validation:

- parser/feature changes: representative real-pattern fixtures plus TF load;
- structural mapping changes: graph invariants and source-accounting tests;
- release/full-corpus work: complete pinned source conversion, deterministic rebuild, browser/API smoke and representative queries;
- Agora contract changes: current Agora schema/host integration test.

Do not hide a failure behind a warning unless the frozen contract says that case is intentionally non-fatal.

## 6. Independent adversarial review

Freeze the implementation head and review it from a logically independent context.

The review asks whether:

- source evidence actually supports the mapping;
- any source semantics are silently dropped;
- synthetic slots fabricate text or distort position;
- repeatable metadata was flattened lossily;
- raw XML/JSON or sidecars became a semantic dependency;
- feature names imply BHSA/DSS semantics that are absent;
- tests prove production behavior;
- complete-source accounting is honest;
- licence/provenance claims are supported;
- documentation matches current behavior.

Any production change after approval invalidates that approval and requires re-review of the new final head.

## 7. Merge and continue

Merge only when acceptance criteria, tests, docs, and final-head review are satisfied. Close the issue and select the next actionable release dependency.

If research exposes a distinct defect or source family, create a focused issue. Do not recursively expand the current PR unless correctness of its stated contract requires it.
