# Issue #64 — pinned controlled-vocabulary audit (first bounded slice)

## Research: real pinned Brown source

The actual `include_taxonomies.xml` (commit
`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, Git blob
`c273ee4f0c8e751fca3274c7ce2d1e6ec5d60637`) contains six
`taxonomy` elements. **XML comments contain 23 additional inactive
`category` tags**. The original issue's string-scanned count of 165
therefore overstates the 142 *active* XML category entries. Examples of
commented-out IDs include `clay.terracotta`, `metal.bronze`,
`stone.travertine` and `magic.defixio` — these are NOT defined targets.

Current `metadata_parser` stores literal `msItem@class` as
`genre`, `msItem@ana` as `religion`, `objectDesc@ana` as
`object_type`, `supportDesc/support@ana` as `material` and
`condition@ana` as `condition`. No taxonomy is passed to
`parse_epidoc_file`. The writer persists source strings verbatim.
Related source values include `#jewish` vs `jewish`. It is
**incorrect** to strip `#` globally before auditing unresolved
values, or to treat taxonomy prefixes/comments as definitions.

## Decision / bounded acceptance

Before any schema/writer rewriting, produce an **authenticated
read-only inventory** of *every distinct observed native TF source
value* for these five fields, with exact target taxonomy, raw
count, precise resolution status and stable deterministic JSON.
Parse only real TEI taxonomy elements (not comments), reject wrong
namespace, duplicate/ambiguous XML IDs, unexpected six-taxon set,
malformed references and taxonomy source identity mismatches.
Resolution: only a bare ID or a single leading `#` plus an *active*
category ID in the field's assigned taxonomy resolves. Unknown,
multiple or cross-taxonomy values stay unresolved; do not guess
case/spelling or insert fake ontology nodes. Preserve original
strings/TF feature values unchanged in this first PR.

## Research → plan → RED TDD → GREEN → tests → independent review

1. RED synthetic TEI `classDecl` tests for 6 taxonomy buckets,
   commented-out category ignored, exact hash pin, duplicate category
   detection, wrong-taxonomy rejection, `#` vs no-`#`,
   not guessing `Clay` / `clay.terracotta` / multiple tokens.
   Offline fake TF node-feature iterator fixture for stable counts.
2. GREEN implement `iip_tf.taxonomy_audit` library + CLI to read
   source `include_taxonomies.xml`, authenticate the **Git blob** ID
   (Git object header + raw bytes), scan the loaded native TF features,
   and emit exact, UTF-8, deterministic audit JSON with active taxa
   metadata and an inventory per field, including unresolved values.
3. Integrate the audit after the *full pinned native TF build* using
   `upstream-iip/include_taxonomies.xml`, preserving original
   authentication of the full source tree and all required build
   gates. Audit output is a diagnostic report, NOT corpus semantics
   or a hidden sidecar used for querying; upload it with reports.
4. A later, separately reviewed #64 slice will decide additive
   `*_original` features and native `taxonomy_category` nodes,
   parent edges and immutable observed-value baseline. No premature
   modification of default source feature values.
5. Run ordinary exact-head CI, authenticated pinned 5,535-record
   double-build, independent skeptical source/code review. Merge only
   after all gates green. Keep issue #64 OPEN after this audit-only
   slice.

This plan specifically guards against categorizing commented-out
taxonomy XML IDs as valid; this is a data correctness issue.
