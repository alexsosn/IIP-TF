# Issue #34 plan — lossless metadata source shapes

## Research gate

Full pinned-source measurement is recorded in `docs/research/metadata-shape-schema.md` and is reproducible with `scripts/research_issue34.py`.

## RED-first contract

Before changing schema JSON/docs, tests require:

- `support_note` in the node-type set;
- `support_note` listed as repeatable metadata, not scalar inscription metadata;
- `metadata_nodes.support_note` with raw `source_key` + `note`;
- parent type `inscription`;
- `facsimile_surface.parent_types` equal to `["inscription", "facsimile_surface"]`;
- researcher docs state one node per non-empty direct `support/p` and preserve nested surfaces.

## Implementation

Make only additive/structure-preserving schema changes. No converter/parser behavior belongs in this ticket; #25 consumes the corrected contract.

## Verification

- schema-contract tests green;
- existing textual IR/full-source regression remains green;
- research workflow still reports max support count 2 and max surface depth 2;
- exact final head receives logically independent adversarial review.
