# Issue #43 plan — preserve zero-span semantic points

Research: `docs/research/zero-span-points.md`

## Research gate

The pinned-corpus audit establishes two different classes of empty spans:

1. empty structural containers (`edition`, `paragraph`) that have no point semantics;
2. empty `markup` nodes that represent a source/projection point and whose exact boundary is currently lost.

The implementation therefore must not solve all empty nodes with one generic anchor.

## RED

Add regression tests before changing production code:

1. native inline markup at beginning, middle, and end of a paragraph preserves a
   record-local boundary offset;
2. zero-atom segmented tokens project onto the corresponding native empty markup
   point and retain the token identity;
3. empty projected markup inside a non-empty token derives a unique boundary
   from mapped neighboring atoms;
4. ambiguous point projection fails closed;
5. IR validation rejects a point outside `0..len(signs)` and rejects a node
   that simultaneously has a non-empty semantic span and a point offset;
6. empty structural edition/paragraph nodes remain `point_index=None`.

The RED commit is expected to fail because `IRNode` does not yet expose
`point_index`.

## GREEN

1. Extend `IRNode` with `point_index: int | None = None`.
2. Extend `InscriptionIR.__post_init__` with point invariants.
3. In the native parser, assign the already-known `start` boundary when an
   inline semantic node emits no signs.
4. In segmented projection:
   - carry native point nodes into the projection lookup;
   - pair zero-atom token annotations to a unique compatible native empty-markup
     point inside monotonic token bounds;
   - for empty projected annotation spans inside a non-empty token, derive the
     point from mapped neighboring atoms;
   - fail closed on contradictory or ambiguous boundaries.
5. Update schema/reference documentation with the IR point-boundary contract
   and the distinction between semantic point vs technical TF anchor.
6. Keep sign population and all frozen node counts unchanged.

## Test gates

- Ruff.
- strict MyPy.
- full pytest suite.
- pinned full-source textual-IR workflow:
  - 5,535/5,535 parsed;
  - exactly 7 researched repairs;
  - 39,472 segmented token identities;
  - frozen node counts unchanged.
- extend the research audit so all 49 empty markup nodes have
  `point_index != None`, while empty edition/paragraph nodes do not.
- exact-head independent adversarial review grounded in the implementation,
  audit output, and representative Brown records.

## #5 hand-off

#43 does not implement the TF writer. #5 must consume `point_index` and prove a
standard TF load round-trip where point nodes are technically anchored but
remain explicitly zero-width. Empty structural nodes use the existing
inscription-anchor policy rather than point semantics.
