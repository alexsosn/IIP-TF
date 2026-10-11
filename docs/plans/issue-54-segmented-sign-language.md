# Issue #54-C — projected Aramaic word language wins over script-like p/@xml:lang

## Source and code research (2026-10-11)

The pinned Brown commit `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5` contains:
- `chor0001.xml` Git blob `f08f433383d889b6afaaf31f93edf1f725b0a9d8`: genuine `p xml:lang="heb"` over Aramaic Hebrew-code-point transcription, and selected `w xml:lang="arc"` in `transcription_segmented` projecting to those original signs.
- `beth0023.xml` blob `1bd3522dc5b6c3d0ac8f4869f8693dcabd541888`: `foreign xml:lang="arc-Grek"` and the corresponding `w`, whose language must not be damaged by `heb` script conversion.
- `sina0114.xml` blob `28a159b5290d0f77e9ea37c4c7c23cd1234f0e51`: Latin transliteration, not a trustworthy basis for inferring the original stone script or language.
- Separate #55 name origin: English `persName xml:lang="egy "` in `caes0044`; do not touch translations.
  
Existing `text_parser.parse_epidoc_file` enriches metadata, then invokes `enrich_segmentation`, which emits selected projected `NodeType.WORD` with source `lang`, `lang_source=transcription_segmented`, `segmentation_status`, `sign_keys` aligned onto original sign slots. Merged #86 adds `IRSign.lang_original` (parser-visible exact source spelling) and `lang_origin` (declaring TEI tag), and preserves inherited source provenance. No need to rematch XML or alter word spans.

## Conservative decision and explicit boundary

Fix only **attested Hebrew-script alphabetic sign slots** in a source `transcription` of `main_lang=arc` when all conditions hold:
1. current `lang=heb`, `lang_original.strip()=heb`, and `lang_origin=p` (script-like paragraph); never clobber inline `foreign`, `persName`, edition-level declarations, another layer, or missing provenance;
2. `encoded_script(glyph) == Hebr` (actual Unicode evidence, not guessed stone script);
3. an aligned, selected, drift-free segmented `word` has `lang=arc` with `lang_source=transcription_segmented`;
4. no disagreeing aligned selected word language on that sign; conflict fails closed with an explicit error.

Effective sign becomes `lang=arc, lang_source=transcription_segmented`. `lang_original`, `lang_origin`, source words, `script`, slots/edges and text formats are unchanged. All uncovered and ambiguous signs remain source-valued and visibly incomplete; **not** full #54 or ISO 639-3 normalisation (#52). Do not assign language based on encoded script alone. Report pinned counts before adjusting scope.

## RED → GREEN → full validation

- RED tests actual EpiDoc→IR→native TF for exact candidate, explicit foreign, unsegmented, wrong-record-language, Greek/Latin, alternatives/non-primary layers, and synthetic slots. Direct IR test overlapping contradictory word annotation fails closed; equal language overlap is idempotent.
- Modify parser's post-segmentation return through an isolated function. Update one #86 regression that intentionally expected uncorrected sign `heb`, and amend ADR/native schema/guide.
- Run Ruff, strict MyPy, pytest, authenticated Brown canary, textual-IR, full 5,535-record TF double-build/reload/reproducibility, browser and existing data gates. Add pinned source-specific validation and source-backed changed-sign reporting.
- Independent adversarial pass on full diff + **independent retrieval of exact pinned XML blobs**. Review must try to falsify sign/word correspondence, attr origin safeguards, repeatability, and unsegmented behavior. Do not merge until exact-head gates and post-gate review pass.

## Still open

#54: record-wide coverage, unsegmented signs, `arc-Grek` separation and reviewed language inventories. #55 name-origin separation; #52 normalization; #57 umbrella; #12 release.
