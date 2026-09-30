# Issue #25 plan — metadata IR

## Research gate

See `docs/research/metadata-ir-parser.md`. The implementation is constrained by schema 0.1,
the pinned metadata audit, #15 repaired input, and #24 canonical textual IR.

## RED-first slices

1. Extend canonical NodeType with all frozen repeatable metadata types.
2. Populate raw scalar inscription metadata and lossless date integer derivatives.
3. Preserve every dimensions record as a node; hand dimensions parent to hand.
4. Preserve repeatable bibliography and biblScope nodes and resolve local textual ana → cites.
5. Preserve decorations without flattening repeated decoNote records.
6. Preserve facsimile surface grouping, graphics, explicit credits/roles, notes, and direct graphics.
7. Preserve revisionDesc/change history.
8. Reject scalar-cardinality violations and unsupported constructs in mapped metadata scopes.
9. Run all 5,535 non-test pinned records through the integrated parser and account metadata nodes.

## Architecture

Add `src/iip_tf/metadata_parser.py` with a pure enrichment function:

`enrich_metadata(ir, root) -> InscriptionIR`

The textual parser remains responsible for source preflight/XML parsing and calls the enrichment
step before returning. The metadata parser may add/replace immutable IR nodes/edges but cannot
modify sign order/text semantics.

Metadata nodes use one existing primary/technical anchor sign and explicit ownership edges.

## Done

Focused tests and pinned full-source metadata validation pass, no repeatable structure is
flattened, no unknown mapped construct is silently ignored, and the exact final PR head receives
logically independent adversarial review.
