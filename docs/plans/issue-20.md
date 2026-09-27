# Issue #20 plan — duplicate segmented-edition resolution

## Goal

Freeze and test a deterministic, source-grounded policy for duplicate
`transcription_segmented` editions before #3 freezes word-node semantics.

## Research gate

Completed in `docs/research/segmented-duplicates.md` from:

- the pinned IIP XML;
- IIP segmentation README and Python pipeline;
- upstream commit history;
- upstream segmentation error logs;
- token-by-token canonical comparison of all three current duplicate records.

## TDD contract

Add a small source-resolution utility, independent of Text-Fabric serialization.

It returns:

- selected candidate index or no selection;
- resolution status;
- all source `change` values;
- suppressed candidate indices;
- explicit conflict fields where a researched override was required.

Required fixture behavior:

- `ashk0016`: stale empty + one non-empty → select non-empty;
- `suhm0001`: semantic duplicate rerun → collapse without semantic loss;
- `zoor0453`: validated pinned-source override → select the pre-rerun `arc` layer and record `xml:lang` conflict;
- unknown structural/token conflict → raise and fail closed;
- changed `zoor0453` conflict shape → override must refuse to apply.

## Implementation boundary

The resolver does not build TF nodes and does not normalize philological language values.
It only chooses which source segmentation supplies word boundaries/token metadata and reports
suppressed source variants.

#3 will define how the resolution provenance appears in the TF schema. #4 will consume the
resolver in the parser.

## Verification

- RED observed before production module exists;
- focused tests and full suite green;
- no changes to generated corpus audit are required unless resolver research changes measured source facts;
- exact final head receives logically independent adversarial review.
