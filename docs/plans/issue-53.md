# Issue #53 — stop applying inscription language to English translations/commentary

## Source-grounded research

In pinned Brown IIP `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`,
translation and commentary `div` elements normally do not declare their
own language. Existing `text_parser.parse_epidoc_file` passes the
record's `textLang/@mainLang` to every native edition via
`header_lang = _Lang(identity.main_lang, "textLang.mainLang")` and
`_parse_edition(..., header_lang=...)` unconditionally. Consequently
English translated prose and English commentary receive `lang=grc`,
`lang=arc`, etc. The pinned corpus audit documents hundreds of
thousands of affected signs (issue #53). This is a semantic mislabel,
not an issue with the display text.

The native `_child_lang` helper already respects `xml:lang` on an
edition/paragraph and records `lang_source=xml:lang` or `inherited`;
it also preserves non-XML parent source tags. The narrow safe fix
is to provide `_Lang("eng", "layer:translation")` or
`_Lang("eng", "layer:commentary")` as the edition fallback *only*
for those two layers, while continuing to call `_child_lang`
so explicit division `xml:lang` takes precedence.
Do not infer English from the characters: this is an explicitly
provenanced converter rule, not source-declared.
Keep raw `textLang/@mainLang` on inscription nodes and
transcription/diplomatic signs. Do not silently normalize source codes
`grc`, `arc`, `he/heb` (#52) or reinterpret
`persName/@xml:lang` origin (#55); both need separate ADR work.

## Research → plan → RED → GREEN → pinned → independent review

1. RED real EpiDoc→IR→native TF fixture with Greek/Aramaic
   inscription language, original transcription, English translation,
   and English commentary. Assert original signs unchanged, prose
   signs `lang=eng`, `lang_source=layer:translation/commentary`,
   and exact visible text/sections preserved. This must fail before the
   parser change.
2. RED separate fixture with `translation xml:lang=la`: source-declared
   language wins, with `lang_source=inherited` on the paragraph signs.
   Test nested inline `xml:lang` overrides where applicable, without
   conflating name origin (#55).
3. GREEN change only edition language fallback policy in
   `src/iip_tf/text_parser.py`; no sign-node changes, source glyph
   changes, extra metadata sidecars or hidden language guessing.
   Update schema reference and ADR language provenance notes; add
   executable pinned source audit for all translation/commentary signs:
   none may carry a record-level mainLang provenance and both
   assigned layer sources must exist. Require exact `bloy0002`
   translation visible and assigned eng.
4. Full exact-head Ruff, strict MyPy, pytest, six-file authenticated
   canary, 5,535-inscription native double-build, independent textual
   IR validation and real browser smoke, then a fresh logically
   independent skeptical code/data review. Do not merge red.
5. Staged #57 language/script/name-origin normalization remains open;
   #53 may close only if issue-specific acceptance is met with pinned
   evidence.
