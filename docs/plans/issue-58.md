# Issue #58 — explicit native TF display format for empty EpiDoc glyph references

## Research

Pinned Brown source `masa0286.xml` contains two empty `<g ref>` elements
(`phoen-gaml`, `phoen-delt`). In IIP-TF the parser retains one
`IRSign(synthetic_kind=glyph_ref,glyph="")` per empty `g`, and a
native `markup(kind=glyph,ref=...)` node with that exact sign key.
`text-orig-full` correctly returns empty: this is a **source reading**,
not a missing Unicode mapping. Issue #58 documents 1,955 empty source
glyph refs in 503 records, including many without unambiguous Unicode
equivalents; Brown IIP old browser used literal `((ref))` notation.

The frozen `_otext()` currently produces `{primary_glyph}{primary_after}`.
Its `primary_glyph` is normalized primary reading, with all alternative
branches excluded. A new `text-orig-refs-full` can use a separate
per-sign native feature `primary_ref_glyph`, copying each already-selected
visible `primary_glyph` unchanged, and substituting **only** empty
`glyph_ref` signs on that primary reading with `((verbatim-ref))`.
The ordinary `primary_after` remains authoritative for spacing.
No source `glyph`, canonical IR, text-orig-full, role selection or
other layer format changes; the format is opt-in and must be documented
as a *display/transcription aid*, not an attested reading.

## Research → plan → RED TDD → implement → test → independent review

1. RED native EpiDoc→IR→TF tests with a Masada-style two-reference
   inscription, mixed real glyphs and both empty and nonempty `g`,
   normalized/source choice branches, diplomatic-only fallback, and
   unsafe-looking `ref` literals. Assert new opt-in format displays
   `((phoen-gaml))((phoen-delt))`, while `text-orig-full` remains
   genuinely empty and `F.glyph` remains undefined on the technical
   zero-width sign. Preserve source ref on markup and exact node slots.
2. GREEN build an index from **native IR markup sign_keys** to the
   referenced synthetic sign, fail closed on duplicate/conflicting
   refs or synthetic/glyph mismatch (rather than picking arbitrarily),
   construct `primary_ref_glyph` using selected `primary_glyph` and
   documented `((ref))` rendering *only* for eligible primary sign
   events. Add `fmt:text-orig-refs-full` to `_otext` metadata, without
   changing its default format order or IR slots.
3. Document the backwards-compatible explicit format in frozen
   schema 0.1 reference and JSON, including source/derived provenance.
   State it does not render refs as Unicode letters and does not fix
   the default `T.text` contract or other layers (#51).
4. Add pinned full-corpus validator on actual `masa0286`, `masa0290`
   and survey all raw `glyph_ref` slots with nonempty `ref`: the
   explicit format must expose all **eligible** normalized-primary refs
   without silently losing already-visible source signs. Keep pinned
   accepted slot/node/edge cardinalities; update feature count iff
   it changes for the new native feature, and explain it.
5. Full exact-head Ruff, MyPy, pytest and authenticated pinned double
   corpus build + browser; independent skeptical review grounded in
   real Brown XML and TF output; merge only when green.
