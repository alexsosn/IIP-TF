# Issue #83 — read-only token-level classification resolution

## Real-source research

PR #82 generated `taxonomy-audit.json` in authenticated pinned
run #176. Of **530** multi-token source attribute *occurrences*
(`genre` 81, `material` 41, `religion` 12, `object_type` 396),
**402** are wholly exact-resolvable as lists of active taxonomy IDs,
**126** have both active and unknown components and **2** contain
no active component. Examples of partial matches include `#dedicatory
#Quotation`, and object terms `household.pottery`, `handle`,
`amulet`, `gem`. The source raw strings are legitimate multivalued
TEI refs and must never be discarded just because the whole string
is not one category ID.

Current `taxonomy_audit.audit_values` emits one `multiple_tokens`
status for the whole raw literal but no component analysis.
This first follow-up changes only the *diagnostic audit*, not the
converter, writer, schema, Text-Fabric features or native semantic
edges. Parent #64 stays open for many-to-many category modeling.

## Research → plan → RED → GREEN → complete corpus test → review

1. RED tests require the full literal `raw`, repeatable token
   entries with original spelling and ordinal index, each exact
   active taxonomy category ID or explicit `unresolved` /
   `wrong_taxonomy` status, and per-field fully/partially/non-resolved
   multivalue attribute occurrence counts. Preserve duplicate tokens.
2. GREEN use the *same* strict source-backed resolver on every
   whitespace token, without casefolding, fuzzy spelling, invented
   category IDs, XML-comment activation or loss of the literal field.
   Single-value `status` and previous `multiple_tokens` rows remain
   backward compatible; additive `tokens` and
   `multivalue_resolution` metadata are diagnostics only.
3. Pinned source run requires **exact** multi-token partition
   `fully_resolved=402`, `partially_resolved=126`,
   `no_resolved=2` across five features at Brown revision
   `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.
4. Full Ruff/MyPy/pytest, authenticated six-source canary,
   5,535-inscription double TF build/reproducibility and local
   browser, independently skeptical exact-head code/data review.
5. Keep #64 open. A later ADR must choose native repeatable
   taxonomy-category relations and what scalar source features
   mean; this PR may not mutate them.
