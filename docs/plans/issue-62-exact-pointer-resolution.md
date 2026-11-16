# Issue #62: exact citation-pointer resolution, staged graph prerequisite

Research: the merged bibliography authority index has 762 exact IIP keys on 767 TEI works, with a genuine two-key work (IIP-001 and IIP-694). Existing inscription bibliography IR nodes retain raw `target` strings. The pinned issue census reports malformed zero-padded targets, untyped `ptr` elements, external identifiers, missing .xml suffixes, and hundreds of keys absent from the stale export. Existing native TF node writer anchors every IR node to an inscription. Shared publication nodes need a separate design decision, so this slice must not introduce a fake per-inscription authority.

Plan: add a pure resolver that consumes one existing `BibliographyIndex` and an untouched pointer target. Permit only exact `IIP-[0-9]+` or `IIP-[0-9]+.xml` spellings. Reject fragment/query/path, leading/trailing whitespace, case variants, malformed or zero-padded *unless that exact key is attested*, and unknown keys. Explicitly attested two-key aliases must return the same publication entry. A missing `ptr@type` must not change lookup. Return an explicit unresolved result retaining the original target and a stable reason, rather than guessing.

TDD: RED commit with positive, negative, alias, and source-preservation tests, verify failure in CI, then implement and run normal CI, full pinned-source Zotero acceptance (already exists), Context-Fabric fixture. Independent adversarial review of the final head before merge.

Later stage (not covered): decide global publication node ownership/anchoring, native `bibl`→publication edges, author/editor source metadata and full pinned 5,535-record resolved/unresolved census. Keep #62 open.
