# Issue #26 plan — segmented projection and parser closure

## Goal

Integrate the #20-selected `transcription_segmented` annotation into the canonical IR without
creating duplicate text slots, then close parent parser issue #4.

## Research gate

Completed in `docs/research/segmentation-projection.md`, grounded in the upstream segmentation
prototype and pinned edge cases including `masa0779`, `mgha0001`, `caes0428`,
`idum0375`, and the three #20 duplicate records.

## TDD gate

Commit RED tests before production projection code for:

- ordinary words and `lb break=no` spanning;
- diplomatic fallback projection including a zero-width `cb` token;
- selected/suppressed candidate provenance;
- apparatus markup annotations;
- no-segmentation behavior;
- ambiguous projection fail-closed;
- repaired-root resolver integration.

## Implementation

1. expose #20 resolution for an already parsed/repaired XML root;
2. build deterministic segmented token/markup atom streams;
3. find a unique monotonic token embedding into primary sign atoms;
4. create segmentation, word, and projected markup nodes/edges;
5. integrate enrichment into `parse_epidoc_file` after textual + metadata IR exists;
6. extend full-source accounting with exact candidate/selected-token counts and zero failures.

## Expected full-source invariants

The audit-only counts exclude the seven malformed files repaired by #15. The end-to-end parser
therefore freezes the repaired-source invariants:

- segmentation candidate/provenance nodes: 5,167;
- selected token identities: 39,472;
- word nodes: 39,463;
- zero-atom token identities represented as markup: 9;
- suppressed duplicate candidates: exactly 3;
- no guessed words in records without selected segmentation.

Any mismatch in these invariants blocks release and requires source research plus a RED fixture
before changing the algorithm.

## Review

Freeze an exact final head, require unit/type/lint + pinned full-source validation, then perform a
logically independent adversarial review focused on ambiguity, coverage holes, provenance, and
selected-inline-markup loss.
