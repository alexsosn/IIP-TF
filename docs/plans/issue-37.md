# Issue #37 plan — align metadata parser with schema #34

## Research gate

See `docs/research/metadata-shape-parser.md` and #34's pinned full-source measurements.

## RED-first behavior

- all four real repeated-support cases produce two independent `support_note` nodes and no inscription `support_note` scalar;
- support-note nodes are inscription-owned and use deterministic source keys;
- `mgha0001`-shape nested surface keeps a direct child-surface parent edge and child image ownership;
- an invented depth-3 surface is rejected rather than flattened.

## Implementation

- add `NodeType.SUPPORT_NOTE`;
- remove `_ordered_prose` scalar support-note path;
- emit native support-note nodes during enrichment;
- factor facsimile surface emission into a bounded recursive helper with max supported depth 2;
- preserve `in_inscription` for both top-level and nested metadata nodes.

## Full-source gate

Extend pinned canonical-IR validation with metadata accounting:

- parsed records = 5,535;
- support_note node count = total non-empty direct support/p count;
- scalar inscription support_note count = 0;
- nested facsimile-surface edge count = 1;
- max emitted source surface depth = 2.

## Review

Exact final head receives logically independent adversarial review before merge.
