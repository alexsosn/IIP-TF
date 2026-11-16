# Issue #62, staged source authority-key index (research and TDD plan)

## Authenticated source evidence

Source: Brown `data-keep/iip-zotero-export.xml`, immutable `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, Git blob `38f7c4d7c8c24756a0023e3e77c7ed6e02b8786d`.

A full, preliminary lexical survey of the source (comments excluded) finds 767 TEI `biblStruct` entries, 761 with at least one `IIP-NNN` identifier and six without. Across those keyed entries there are **762 distinct IIP keys**: one *actual single work* (Abel, *Tombeau et Ossuaires Juifs Récemment Découverts*) explicitly carries both `IIP-001` and `IIP-694`. The source uses both `monogr/idno[@type='callNumber']` (`IIP-380`) and `note[@type='tags']/note[@type='tag'][@xml:id]` (`IIP-609`). An unrelated tag such as `IEJ1995d` on the latter is not evidence for converting arbitrary external identifiers to IIP keys. This lexical survey is provisional until validated via a namespace-aware parser in actual CI.

Existing inscription `bibl` nodes carry original `target` including `.xml`, not an authority link. Existing `tf_writer` requires an inscription owner and source span for every native node: globally shared publication nodes cannot be introduced without a considered anchoring/ownership ADR. Stale export and malformed bibliography targets remain unresolved.

## Scoped decision

This PR prepares a **read-only source-authenticated exact IIP-key index**, one record per authentic TEI `biblStruct`, with multiple *explicitly attested* keys allowed for the same work. One key appearing on two separate works is a fatal ambiguity. Preserve author/title semantics for a later native graph slice: the index must not resolve inscription references or construct TF nodes yet. Avoid fuzzy spelling, zero-pad coercion, inferred edition merging, reassigning existing `bibl` nodes, or treating unkeyed entries as linked. Source key extraction must be scoped to the correct TEI parent and use an XML parser, not regex or full-text matching.

## RED-first tests, implementation and gates

1. Commit failing tests before implementation. Realistic namespaced TEI fixture includes the observed call-number-only journal, note-tag IIP-609 plus non-IIP short tag, two **same-publication** IIP aliases, a truly unkeyed entry, misleading other-id/callNumber positions, and unrelated XML comments. Verify title provenance as analytic/monograph separately, sorted unique source entries, exact-match lookups.
2. Negative tests: same key on two distinct `biblStruct` must raise, changed source Git blob rejects, symlink and malformed/wrong namespace fail, unsupported nested `biblStruct` structure rejected, and `IIP-0119` is never guessed as `IIP-119`.
3. Add the smallest pure reader API (no corpus or GUI behavior changes) and run focused GREEN plus normal Ruff, strict MyPy, pytest. Read/authenticate whole pinned source in CI to confirm real counts.
4. Logically independent adversarial review of exact-head source file, fixtures and CI before merge.

## Separate follow-up (issue #62 stays open)

Decide a native authority graph/ADR compatible with Text-Fabric anchoring and licence/provenance. Materialize repeatable source authors/editors, journal/book titles, imprint and source IDs, resolve original IIP `bibl.target` exactly (including the narrowly specified `.xml` pointer syntax), and retain unresolved targets. Authenticate complete pinned native build, browser, raw/compiled CFM and query "inscriptions citing Rahmani 1994" before closing #62.
