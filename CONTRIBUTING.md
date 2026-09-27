# Contributing

IIP-TF uses issue-driven development.

Before opening an implementation PR:

1. read `AGENTS.md`, `research.md`, `design.md`, `plan.md`, and `LICENSE_SCOPE.md`;
2. select or open a focused GitHub issue with acceptance criteria;
3. check for overlapping issues/PRs;
4. research current upstream behavior when the task depends on IIP/EpiDoc, Text-Fabric, or Agora;
5. for behavior changes, preserve a RED regression before the production fix;
6. run focused tests and the relevant full suite;
7. update researcher documentation when the public corpus contract changes;
8. obtain a logically independent adversarial review of the exact final head.

## Pull requests

Keep one implementation concern per PR. Link the issue and include:

- source/research evidence used;
- the RED test or reason the change is documentation-only;
- exact test commands/results;
- corpus/full-build evidence when relevant;
- user-facing documentation impact;
- known limitations.

A reviewer should actively look for silent source-data loss, guessed philological semantics, opaque blobs/sidecars, invalid TF anchoring, non-determinism, misleading BHSA/DSS compatibility, licensing mistakes, and tests that only exercise fixtures rather than the production path.

See `docs/agentic-dev-loop.md` for the full autonomous workflow.
