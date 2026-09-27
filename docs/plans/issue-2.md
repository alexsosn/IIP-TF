# Issue #2 plan — corpus-wide IIP/EpiDoc reconnaissance

## Research question

Before the TF schema is frozen, measure what the pinned Brown IIP source actually contains. The output of this issue is evidence, not converter behavior.

## Source

Pinned candidate release source:

- repository: `Brown-University-Library/iip-texts`
- revision: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`
- source directory: `epidoc-files/`

The pin may be changed only by an explicit follow-up issue; all committed inventory artifacts must state the exact revision they describe.

## Method

Implement a deterministic offline audit module that accepts a local `epidoc-files` directory and emits one canonical JSON object. A human-readable Markdown report is rendered from that same object.

The audit must measure:

1. file accounting and parse failures;
2. IIP/XML identity;
3. language declarations;
4. transcription presence and `transcription_segmented` coverage;
5. empty transcriptions and line breaks;
6. `textpart` usage;
7. element and attribute inventories by major semantic context;
8. repeated metadata cardinalities relevant to node-vs-feature decisions;
9. licence/DOI evidence;
10. source constructs that require explicit schema decisions in #3.

## TDD gate

RED tests define the inventory contract using small EpiDoc fixtures before the audit implementation is added. The fixtures cover:

- segmented and unsegmented text;
- Greek/Hebrew/Aramaic language declarations;
- editorial markup and line breaks;
- repeated bibliography/hand/facsimile structures;
- an empty inscription;
- malformed XML;
- CC BY-NC + DOI evidence.

## Full-corpus gate

A GitHub Actions research job checks out the pinned Brown source and runs the audit. It uploads the generated JSON/Markdown and prints a compact summary.

The committed `docs/research/iip-inventory.json` and `docs/research/iip-corpus-audit.md` must be generated from that exact pinned source and then checked for byte-for-byte freshness by CI.

## Acceptance

- deterministic unit tests pass;
- whole-source audit completes and accounts for every `epidoc-files/*.xml`;
- committed JSON and Markdown match a fresh audit of the pinned source;
- report calls out rare/ambiguous constructs instead of hiding them;
- licence conclusion distinguishes observed per-record statements from project-wide inference;
- exact final PR head receives independent adversarial review.
