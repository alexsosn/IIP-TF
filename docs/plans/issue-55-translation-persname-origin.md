# Issue #55-A — Translation personal-name language origin

## Authenticated research

Pinned Brown source revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`:
- `epidoc-files/caes0044.xml`, blob `6d5b753600715e305675a514994d1d7c8315ad54`, translation lines 160–162: `<persName xml:lang="egy ">Cleopatra </persName>`.
- `epidoc-files/hamm0054.xml`, blob `06b4c9cedc109ea807bc905efc51d3280a7a1f55`, translation lines 148–151: `<persName xml:lang="x-Arabic ">Abdallah Mu'awiya</persName>`.
- `epidoc-files/beth0117.xml`, blob `74c56fe08bd9d992a946264c6f0a0a8d677dadf0`, translation lines 121–124: `<persName xml:lang="grc ">Arethas</persName>, <persName xml:lang="x-Nabatean " type="aka">Hareth </persName>`.

Current `_parse_inline()` calls `_child_lang(element, parent)` unconditionally, and passes the name's origin label as `lang` into its glyphs/descendants. The entity node also gets `lang` from `_mapped_features()`. This labels *English translation characters* `egy`, `x-Arabic`, `x-Nabatean` and makes them answer text-language queries. Merged #86 already preserves exact `xml:lang` raw spelling in `lang_original` and its declaring tag in `lang_origin`.

## Scoped design

Only in `Layer.TRANSLATION`, an explicit `persName/@xml:lang` is **name origin**, not language of the translated text:
- `name_lang` on the `persName` entity: issue #55's maintainer-approved mapping: `x-Nabatean`, `x-Palmyran`→`arc`; `x-Arabic`→`ara`; `x-Semitic`,`x-greek-hebrew`→`other`; `x-unknown`→`unknown`; `he`,`heb`→`heb`; `la`→`lat`; already ISO 639-3 codes `hbo`,`grc`,`arc`,`egy`,`xcl` unchanged. Strict rejection of unknown explicit codes rather than silently guessing.
- `name_lang_original`: exact parser-visible attribute string including spaces. Existing `lang_original` / `lang_origin` on the entity retained for backwards-compatible source provenance, but **entity `lang`/ `lang_source` omitted** so name-origin codes do not collide with text-language queries.
- The name's signs and ordinary descendant characters **inherit the surrounding translation language** (typically `eng`), while genuinely explicit nested text constructs such as `foreign/@xml:lang` override the parent as before. Tail remains in parent language.
- Non-translation `persName`, `rs`, `name`, words, foreign, all source XML, and Unicode `script` unchanged in this bounded slice. Do not generalize `rs/@xml:lang` without separate source inventory.

## RED → GREEN → validation and review

Commit RED tests for actual XML→IR→native TF with `egy `, `x-Arabic `, `x-Nabatean `, `hbo `, nested foreign, parent language, and non-translation control. Document if the RED Action is canceled or static-analysis preflight blocks pytest. Implement only after tests committed. Do not touch slot topology/text, and amend schema+ADR. Full authenticated Brown 5,535-record native double build/reload (reproducibility, browser, taxonomy), textual IR where applicable, Ruff, strict MyPy, unit tests and source cases. The pinned gate should inspect all observed name origin codes, fail closed if any unmapped. Perform independent adversarial review on actual diff and re-fetched source *after* all final-head gates; no merge otherwise.

This does **not** claim to close #55 or #57: `rs`/non-translation semantics require their own inventory and reviewed rules. Separate PR #88 #54 audit must merge independently.
