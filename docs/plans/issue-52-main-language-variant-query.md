# Issue #52 — Source-preserving, explicitly scoped language-variant queries

## Research (immutable Brown source, project code, external code authority)

- Brown `iip-texts@0b7dc8358ccdfd0c9391f049da4839fbd91c26e5` has mixed source codes. The audit in `docs/research/iip-corpus-audit.md` counts `textLang` declarations `he=475,heb=4`, `geo=2,Geo=1`, `la=300`. **These are declarations, not guaranteed native `main_lang` inscription counts**. Existing #52 pinned TF report separately records `F.main_lang he=405,heb=4` (409 distinct inscriptions). The source token `xml:lang` inventory `he=1793,heb=529,la=2121,lat=22` is likewise *not* native sign `F.lang` after #54 word-supported Aramaic corrections.
- The production `metadata_parser._scalar_metadata` reads `msContents/textLang@mainLang` into **original** `main_lang`. `tf_writer` retains it on `inscription` nodes. `language_resolution.py` explicitly warns that `xml:lang=heb` on transcription containers can be script-like even when the underlying language is Aramaic, so a blanket `F.lang he|heb` semantic-language search is **not warranted**.
- Library of Congress ISO 639 list: Hebrew `heb` (ISO 639-3) / `he` (ISO 639-1), Latin `lat` / `la`, Georgian `kat` (ISO 639-3)/ `geo` (legacy bibliographic form; Brown also has uppercase `Geo`). Sources: https://www.loc.gov/standards/iso639-2/php/English_list.php and https://www.loc.gov/aba/pcc/scs/documents/ISO-639-3-guidelines.pdf .
- Unknown/mixed `Other`, `x-unknown`, and `arc-Grek` must not acquire a guessed language ID. `other_langs` is often a **multi-valued source string**, so `F.other_langs.s(token)` is not a complete set-membership query without parsing; it is **out of scope** for the mainLang exact-value helper.

## Decision and staged plan

Use **query-time source-code union** on **inscription `main_lang` only**, not an additional canonical TF feature. This avoids silently changing source language classifications while the independently tracked script/Aramaic language issues #54/#92 are unresolved. Explicitly document the decision and future possibility of a derived ISO feature after #54, as permitted by #52.

1. RED-first tests on genuine native TF fixture EpiDoc `textLang@mainLang` codes `he,heb,la,lat,geo,Geo,arc`. The new public `find_inscriptions_by_main_language(api, iso3)` must return deterministic native inscription node IDs for `heb,lat,kat` via exact native indexed `F.main_lang.s(raw)` unions. Preserve source `F.main_lang` bytes. Explicitly reject unsupported canonical IDs and missing node feature rather than return plausible empty sets. Inscription only, no sign language guessing. Test real NodeType and output sort/dedup.
2. Implement additive query helper in existing `iip_tf.researcher_queries`; no converter/schema changes or runtime network.
3. Document source-vs-native observed counts, separate `main_lang` vs `F.lang` semantics, and worked copy-paste Python and Text-Fabric native search examples in researcher guide. Do not imply `F.lang=heb` covers all Hebrew linguistic data.
4. Authenticated full pinned native/browser validation: after reloading complete TF, assert 405 `he` and 4 `heb` and union exactly 409 inscription nodes, report `la/lat` and `geo/Geo` source counts and verify alias helper's membership is set equality. The source revision must remain frozen and no native source feature or topology change. Existing full native TF double build, Context-Fabric raw/compiled parity, browser smoke and code gates remain mandatory.
5. Logically independent adversarial code/source review before merge, explicitly examining distinguishing script-like source codes, `Other`, mixed cases, incomplete multi-valued `other_langs` and any incorrect provenance claim. E2E GUI-agent release check remains issue #12.

Non-goals: global ISO mapping, Unicode-script inference of language, rewriting `main_lang`, treating `name_lang` as text language, or conflating sign `lang` with source `textLang`.
