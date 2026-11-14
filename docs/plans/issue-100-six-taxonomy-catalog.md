# Issue #100 (follow-up) — Six-taxonomy catalog from authenticated Brown TEI

## Research (verified against actual immutable source, 2026-11-15)

Source: Brown-University-Library/iip-texts at `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`; `include_taxonomies.xml` Git blob `c273ee4f0c8e751fca3274c7ce2d1e6ec5d60637`.

Directly re-read source XML, stripping comments before counting **active** elements. Six `taxonomy` declarations and 142 active categories: IIP-form 58, IIP-materials 16, IIP-genre 35, IIP-preservation 7, IIP-writing 22, IIP-religion 4. There are 39 active category IDs containing a dot; **38** have an active same-taxonomy prefix, while `IIP-preservation/fragment.single` has no active `fragment` category. All active category elements are direct children of their taxonomies; dotted ID spelling is **not** a TEI parent or `is_a` edge. `IIP-materials/stone.other` is active with `catDesc="Other Stone"`, while `clay.terracotta` appears **only inside a comment**. IIP-writing contains `impressed.inscribed.chiseled` with catDesc `Impressed (Chiseled)`. The source `category/@ana` can encode unrelated authority references; this bounded catalog outputs only active ID and `catDesc` label, without claiming extra authority relations.

Existing PR #102 introduced `parse_taxonomies`, `lookup_taxonomy_labels`, and the `iip-tf taxonomy-lookup` CLI for five normalized inscription features. It intentionally left direct six-taxonomy browsing for this issue. The converter must **not** create synthetic TF taxonomy nodes, sidecars, guessed hierarchical edges, or network runtime dependencies.

## Plan and RED → GREEN gates

1. Add `catalog_taxonomies(registry, taxonomy_id=None)` to existing `taxonomy_lookup.py`. No new parser. It returns deterministic JSON-compatible structures with active category ids and source `catDesc` labels for all six taxonomies, or one explicitly requested taxonomy. Use a single tested helper for dotted-prefix candidates shared with `lookup_taxonomy_labels`; no parent/is_a claims. Reject unknown taxonomy IDs rather than silently producing empty results.
2. Add researcher CLI `iip-tf taxonomy-catalog SOURCE_XML [--taxonomy-id IIP-writing] [--source-revision PIN]`; require exact pinned Git blob if revision asserted; otherwise report null revision and the actual blob hash. No source edits. Explicitly identify `TEI catDesc` as the label source and `dotted_prefix_candidate` as *naming only*.
3. RED-first tests **before implementation**: all six scopes, sample pinned-synthetic `IIP-writing` category, 6/142 authenticated source counts; prefix candidate with or without active prefix; commented-out `clay.terracotta` absent; exact deterministic output; invalid scopes and forged pinned blob rejected. Tests must reach actual pytest RED (not be interrupted by Ruff/Mypy); bounded temporary test job if needed.
4. CI: authenticated preflight existing pinned source taxonomy smoke verifies all six catalog output categories and 39/38 candidate arithmetic; no additional external fixture fetching. Update end-user guide with CLI and Python usage, provenance, and hierarchy limits.
5. Exact-head CI, strict typing, fixture tests, full pinned 5,535-record reproducible native TF + browser + raw/compiled Context-Fabric, and logically independent adversarial review grounded in real source and code. No merge before gates. Separate autonomous GUI release E2E under issue #12.

Non-goals: asserting a conceptual hierarchy, aggregating class counts into claims about physical objects, automatic correction of source IDREFs, importing commented categories, extracting `person.faith`, or changing native TF graph.
