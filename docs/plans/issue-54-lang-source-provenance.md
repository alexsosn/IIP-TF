# Issue #54 — source-language provenance prerequisite (bounded slice)

## Research (2026-10-11)

The real pinned Brown IIP sources (revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`) show incompatible interpretations of TEI language attributes:

- `chor0001`, blob `f08f433383d889b6afaaf31f93edf1f725b0a9d8`: paragraph `xml:lang="heb"` on Hebrew-script Aramaic; selected segmented `w` labels the text `arc`.
- `beth0023`, blob `1bd3522dc5b6c3d0ac8f4869f8693dcabd541888`: explicit `foreign xml:lang="arc-Grek"`, linguistically Aramaic and encoded in Greek letters.
- `sina0114`, blob `28a159b5290d0f77e9ea37c4c7c23cd1234f0e51`: Latin transliteration, with segmented `Other` source code.

Current `_child_lang()` strips source whitespace and remembers only `xml:lang` versus `inherited`. On a sign from a `p` and a sign from a `foreign` this loses the originating element and exact source attribute (including trailing spaces); without those, a later #54 override can corrupt explicit foreign text language. The selected `WORD` nodes do preserve their own clean `lang` but do not retain the original attribute string. This is distinct from #55 name-origin semantics and #52 ISO language normalization.

## Plan and scope

1. RED tests first: actual EpiDoc parser to IR to native TF; explicit `p` vs `foreign` vs inherited source, trailing whitespace, default `textLang` and translation-layer inference, original-text byte invariance and selected segmented word origin.
2. Add sparse `lang_original` (literal XML parser attribute value, not the cleaned language code) and `lang_origin` (nearest explicit source element tag) to sign slots and existing language-bearing markup/container nodes. For selected segmented words annotate source raw language with `lang_original` and `lang_origin=w` or `num`. Carry the originating tag across descendants without inventing an explicit attribute. No synthetic original for converter-inferred languages.
3. Preserve all existing `lang`, `lang_source`, `script`, `script_source`, glyph/after, reading roles, alignment, nodes and text formats. No change yet to problematic Aramaic `lang=heb`, to classification values, or to name-origin semantics. Source XML entity expansion / XML attribute normalization is not byte-level XML serialization: the feature describes the parser-visible raw attribute string.
4. Update schema, ADR and reference docs, run CI Ruff / strict MyPy / pytest, authenticated Brown canary, 5,535-record double-build and textual-IR gate on exact PR head.
5. Independently skeptical review from the complete diff and real pinned examples; correct defects before merge. This is a prerequisite slice; #54 and #57 stay open.

## Independent reviewer attack surface

- Does a nested `foreign` correctly replace a parent `p`'s provenance? Does the parent resume after the child?
- Are `lang_source=inherited` and the explicit origin kept separately? Are no fake `lang_original` values inferred from `textLang` or from an English-layer fallback?
- Do word annotations survive source drift/segmentation without overwriting sign language?
- Do native feature writers report exact original string, with no changed default text or synthetic glyphs?
- Any new source values unsupported or unaccounted? Never interpret this PR as a completed language correction.
