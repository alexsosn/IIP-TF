# Auditing pinned IIP controlled vocabularies

The pinned Brown IIP source at `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`
includes `include_taxonomies.xml`: six declared taxonomies. **There are 142
active `category` XML elements, not 165.** The additional **23** category-like
tags are inside XML comments; for example `clay.terracotta`,
`stone.travertine`, `metal.bronze` and `magic.defixio` are *inactive*.

The taxonomy audit authenticates the exact upstream XML using Git blob ID
`c273ee4f0c8e751fca3274c7ce2d1e6ec5d60637`. It parses XML elements
rather than using regular-expression matches that would include comments.

## Run on an authenticated local native TF build

From the IIP-TF checkout root after following the
[authenticated native build guide](local-tf-browser.md):

```bash
python -m iip_tf.taxonomy_audit \
  upstream-iip/include_taxonomies.xml \
  build/pinned-tf \
  build/pinned-tf-reports/taxonomy-audit.json \
  --raw-original
```

The pinned GitHub Actions native-TF workflow also runs this after
authenticating and building the full 5,535-inscription corpus, uploading
`taxonomy-audit.json` alongside its deterministic build reports.

## What the audit means

The resulting `taxonomy-audit.json` contains each active taxonomy ID,
its exact active category IDs and labels, and a complete inventory of every
distinct raw TF value, including frequencies and resolution status, for
these five source inscription features:

| Native source feature | Brown taxonomy |
|---|---|
| `object_type` | `IIP-form` |
| `material` | `IIP-materials` |
| `genre` | `IIP-genre` |
| `condition` | `IIP-preservation` |
| `religion` | `IIP-religion` |

The sixth `IIP-writing` taxonomy is fully authenticated and inventoried
as a vocabulary but is **not automatically assigned** to an unrelated
source feature. That assignment requires explicit source-field research.

Only an exact active category ID (`jewish`) or its single leading
reference marker (`#jewish`) resolves. A value belonging to another
taxonomy is marked `wrong_taxonomy`; a string containing multiple
whitespace-separated tokens is `multiple_tokens`; all other values
are `unresolved`. The output retains the original raw strings even
when a value resolves.

For source attributes containing multiple space-separated references
(e.g. `#door #lintel` or `#jewish #other_religion`), `values[].status`
remains `multiple_tokens` for backwards-compatible raw-value reporting.
Each `values[].tokens` entry now separately preserves the original token
spelling, its **source order index**, exact category ID if active in the
correct taxonomy, and its `resolved`, `wrong_taxonomy` or
`unresolved` status. Duplicate tokens are retained, never deduplicated.
Each field and the overall report also supply `multivalue_resolution`
with **fully_resolved**, **partially_resolved** and **no_resolved**
counts of *source attribute occurrences*.

The authenticated 5,535-record Brown snapshot contains **530**
multi-valued classification occurrences: **402 fully resolved, 126 partly
resolved, and 2 with no active target**. The pinned audit gate requires
this exact partition for the current source revision. A source revision
change must be explicitly researched, not silently accepted.
Most multi-token attributes are legitimate repeatable taxonomy references,
so a single normalized scalar per inscription would discard real data.
A future native model needs repeatable relations rather than guessing or
flattening categories.

**This diagnostic audit does not normalize or replace the existing native
source features.** In particular it does not guess capitalization, remove
arbitrary spaces, match category descriptions to IDs, treat commented-out
taxonomy entries as active, or materialize semantic sidecars. A later issue
#64 implementation slice must decide the native `taxonomy_category`
nodes/edges, `*_original` feature policy, hierarchy, and immutable pinned
unseen-value baseline with an explicit ADR and separate tests.

The upstream XML and corpus metadata retain Brown's **CC BY-NC 4.0**
source-data terms; MIT applies to the converter code, not source
taxonomy content. Cite the IIP editions and data DOI
[10.26300/pz1d-st89](https://doi.org/10.26300/pz1d-st89).

## Source-normalized native features (issue #64)

The *auditor itself* does not normalize or alter corpus data. Native full-Brown conversion now uses the authenticated taxonomy to populate canonical taxonomy IDs in `F.religion`, `F.genre`, `F.material`, `F.object_type`, and `F.condition`. Their exact verbatim EpiDoc source strings are preserved separately in the corresponding `_original` node features. The `--raw-original` option audits these source fields rather than already-normalized IDs, so the established 402/126/2 multivalue inventory and source provenance remain comparable with previous builds. Fully resolved whitespace-separated source IDREF lists retain their original ordering and repetition as space-separated canonical IDs; **partly** resolved lists have no normalized primary classification, but retain complete `_original` and appear in the audit. The normalized features are only available when the converter has the taxonomy XML; standalone EpiDoc-only conversions without it retain unnormalized source fields. This is a deliberate mode distinction, not an implicit network lookup.
