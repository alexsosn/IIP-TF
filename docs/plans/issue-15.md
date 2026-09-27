# Issue #15 plan — fail-closed source conflict repair

## Goal

Make all seven pinned malformed IIP records parseable without generic recovery, data dropping, or choosing a scholarly reading.

## Research gate

See `docs/research/source-conflict-repair.md`. The conflict history and both sides of every current block have been inspected.

## RED-first contract

Add grounded fixtures for all seven current conflict shapes and tests proving:

- each known pinned file is repaired and parses;
- the union repair preserves the parent facsimile baseline plus non-conflicting stashed metadata;
- duplicate image elements are not introduced;
- unknown conflict-marker files fail closed;
- a changed known conflict block fails closed;
- the repair refuses marker-bearing files on any non-pinned revision;
- a well-formed future-revision file passes through unchanged;
- repair provenance is explicit.

## Implementation

Create a narrow source-repair module. It accepts source text/path plus declared revision and returns repaired text + provenance. It does not perform EpiDoc conversion.

A directory validation command will scan the pinned `epidoc-files` tree and prove:

- 5,536 XML files accounted;
- exactly seven repairs;
- all 5,536 become well-formed after the known repair policy;
- `aaTestFile.xml` remains a source file but is not reclassified by this utility.

## Full-source gate

Add a read-only GitHub Actions workflow that downloads the immutable Brown source tarball and runs the directory validator. No workflow self-push.

## Done

Issue #15 is complete only when unit tests, strict typing/lint, and the pinned full-source repair validation pass on the exact final head, followed by logically independent adversarial review.
