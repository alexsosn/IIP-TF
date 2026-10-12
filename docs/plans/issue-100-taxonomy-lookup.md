# Issue #100 — source-authenticated taxonomy lookup (first user-facing slice)

## Research (2026-10-12)

- Brown IIP source: `Brown-University-Library/iip-texts@0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, `include_taxonomies.xml`, Git blob `c273ee4f0c8e751fca3274c7ce2d1e6ec5d60637`. Existing `taxonomy_audit.parse_taxonomies` authenticates this blob, six TEI taxonomies and 142 active category IDs. Its registry maps each active ID to the `catDesc` human label.
- Source examples: active `IIP-materials/stone.other` = `Other Stone`; active `IIP-materials/stone` = `Stone`; `clay.terracotta` is in an XML comment only; `IIP-genre/funerary.epitaph` has its own literal label. There are **39 active dotted IDs**, but only **38** have an active same-taxonomy dotted prefix. `IIP-preservation/fragment.single` has **no** active `fragment` category. Active `category` elements are siblings, so dots provide **no authoritative TEI parent edge**. No source-backed `is_a` edge will be produced.
- The native inscription corpus has canonical multi-IDREF string features (`religion`, `genre`, `material`, `object_type`, `condition`) plus raw `*_original` data. Existing audits show all-or-nothing normalization; a researcher can split canonical IDs, but cannot directly ask their category labels.
- Source comments are not authoritative declarations; a commented category-looking string must never be interpreted as an active ID. The first slice reports it as unknown, with explicit documentation rather than claiming it was formally deprecated or retired.
- This issue's full scope also considers explicit comment-only provenance and hierarchy candidates, which should not be inferred without evidence.

## Plan and gates

1. Expose a deterministic library function using the existing `TaxonomyRegistry` and `FEATURE_TAXONOMIES` maps, accepting an observed classification field and its exact raw IDREF string; return ordered per-token statuses and **labels only for exact, active, in-scope IDs**. Differentiate `wrong_taxonomy`, `case_mismatch`, `unknown`; leave empty input empty. No fuzzy normalization and no partial canonical output. A dotted category without an active prefix must not emit a candidate.
2. Expose a small `iip-tf taxonomy-lookup SOURCE_XML FEATURE RAW_VALUE` CLI which prints deterministic JSON. Require `--source-revision` to authenticate pinned runs (blob validated for the pinned source); unpinned inputs display their computed source blob and `source_revision=null`, not a false pin claim. The CLI is diagnostic only and does not alter TF data.
3. RED-first tests: multi-IDREF order and duplicates, `#` references, wrong taxonomy, case mismatch, comment-only ID, valid dotted source label without inferred `parent`, absent and invalid source, JSON repeatability, pinned blob rejection, and existing native TF round trip unaffected. Assert real source labels in pinned CI.
4. Run exact-head Ruff, strict MyPy, pytest, native 5,535-record build/reload if triggered, then independently review actual diff/TEI/source semantics. No merge on failed or unknown gates.

## Scope boundary

This PR creates no taxonomy TF nodes or speculative ontology hierarchy, no semantic sidecar, no source modification, no person/inscription/sign changes. Follow-on work for comment-only distinction and sourced hierarchy remains on #100 until independently demonstrated.
