# Issue #90 — Aramaic Hebrew-script transcription under `div/@xml:lang=heb`

## Research, pinned original evidence (2026-10-11)

Parent issue #54, merged inventory PR #88 `76845ed9d3dce6e05e2467c3091dfc525d7fdf4d`, full pinned native Actions #38146732859 (5,535 records, double reproducible native TF). In 1,781 Aramaic records, 5,159 Hebrew-script signs with source `p@heb` already corrected by selected `w@arc`, while 40,003 signs remain source-valued `heb`. 32,220 remaining signs derive from a nonparagraph source declaration. **Not all are safely correctable:** this bucket includes varying encoded scripts, alignment states, languages and source scopes. Across all remaining signs, clean aligned selected word labels counted 31,712 `arc` and 218 `heb`, a *different* measurement and not proof that each is division-scope.

Authentic pinned Brown `epidoc-files/abil0001.xml` blob `a2a40b1ed15a0edfa2fc647a7cc868763ca650ac`: `mainLang=arc`, `<div type="edition" xml:lang="heb" subtype="transcription">`, and aligned `<w xml:lang="arc">דכיר</w>` and further segmented Aramaic words. `chor0001.xml` blob `f08f433383d889b6afaaf31f93edf1f725b0a9d8` remains paragraph-source control; `bshe0157.xml` blob `e7378fe1d70d8ed5e35b2247d28d2a3354ff627c` exemplifies unsegmented signs; `beth0023.xml` blob `1bd3522dc5b6c3d0ac8f4869f8693dcabd541888` explicit `foreign@arc-Grek`, not subject to override.

Current `resolve_sign_languages()` already uses **selected, projected, drift-free source word languages** and rejects conflicting clean overlaps; it restricts `lang_origin=="p"` in `_eligible()`. Its `lang_original` and `lang_origin` preserve original EpiDoc independently from modified effective `lang`. `AramaicLanguageAudit` checks correction evidence but restricts corrected source origin to paragraph too.

## Scoped decision

Extend **only** the source candidate origin in `_eligible` to `p` **or** `div` *provided all other unchanged requirements hold*: `main_lang=arc`, `Layer.TRANSCRIPTION`, effective `lang=heb`, source `lang_original.strip()=heb`, `lang_source=xml:lang|inherited`, **Hebrew Unicode alphabetic** glyph, selected `NodeType.WORD` with clean projected `lang=arc` and no overlap with uncertain or contradictory word. Source `foreign`, `persName`, other record languages, diplomatic/translation, Latin transliteration, unsegmented/untagged/mismatched words, punctuation and technical signs abstain unchanged.

An override preserves `lang_original=heb`, `lang_origin=div`; effective `lang=arc`, `lang_source=transcription_segmented`. No TF nodes/edges/slots/formats change. **Do not** equate Unicode script with original inscription script. No automatic inference from `mainLang` alone.

Update audit's *corrected-sign evidence check* for both approved origin scopes and add breakdown by `lang_origin`; keep mutually exclusive post-correction reasons, bounded examples, deterministic top records. Pinned validator must compare independently calculated corrected sign count with parser + native TF and preserve explicit *paragraph* canary counts, adding division canary from authentic `abil0001`. Replace obsolete exact 5,159 total gate with an evidence-based **paragraph slice == 5,159** and checked overall arithmetic `corrected+remaining==45,162` on the authenticated full source, not on synthetic 1-record failure-ledger tests. Exact *division* corrected count must come from **executed** pinned report; don't guess.

## Research→RED→implement→test→independent adversarial review

1. Commit RED tests before implementation. Synthetic EpiDoc→IR→TF with div-`heb` selected `w@arc`; negative controls for no segmentation, `w@heb`, untagged, drift, nested explicit foreign, other record mainLang, Greek/Latin characters, Arabic/Greek source scripts, wrong layers; verify source provenance + bytes/slots + output.
2. Reuse and minimally extend `resolve_sign_languages`, audit + validated `abil0001` canary, schema/ADR semantics. New native pinned full-report counts guard sign cardinality and 5,159 paragraph slice. Preserve all #88 diagnostics and #89 name origin when integrating branches after #89.
3. Ruff + strict MyPy + pytest, real six Brown source canaries, native pinned 5,535 records and independent **double parse+TF build**, byte-for-byte file hashes, browser/taxonomy and textual-IR checks.
4. Perform a **logically independent adversarial** pass of the exact-head code/real Brown source and final category histograms, intentionally searching for foreign/punctuation leakage, drift, double-counting, conflicting word authority, report masking, and concurrency conflicts. No merge before exact-head green gates and post-gate review.

The umbrella issue #54 remains open; #55 separate. PR #89 modifies the same pinned script: integrate without dropping either source-name or Aramaic audit reports; prefer finishing #89 first.
