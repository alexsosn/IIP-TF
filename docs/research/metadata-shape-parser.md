# Research — implementing metadata shape correction

Issue #37; depends on #34.

The merged #25 parser predates #34 and has two now-known contract violations:

1. `_ordered_prose()` joins all non-empty direct `support/p` values with a blank-line delimiter and stores the result as inscription scalar `support_note`.
2. facsimile surface validation permits only `desc`, `graphic`, and `note` children, so `mgha0001`'s nested child `surface` cannot be represented.

Full-source #34 research proves the supported source boundary:

- non-empty direct support paragraphs occur in 1,512 records;
- exactly four records have two paragraphs and no record has more than two;
- only `mgha0001` contains nested surfaces;
- maximum pinned-source surface depth is 2.

Therefore the implementation can be strict without a generic recursive unlimited schema:

- one `support_note` node per non-empty direct `support/p`;
- top-level surface parent = inscription;
- depth-2 child surface parent = containing surface;
- depth > 2 fails closed until researched.

Source-key XPath-like paths retain note/surface order deterministically.
