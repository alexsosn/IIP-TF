# Issue #94 — research plan for editorial alternatives among 179 uncovered signs

## Grounded Brown source (immutable pinned revision)

Pinned `Brown-University-Library/iip-texts` at `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`; `epidoc-files/bshe0157.xml` blob `e7378fe1d70d8ed5e35b2247d28d2a3354ff627c`, lines 125–126:
`<choice><orig>אבידתה</orig><reg>עבידתה</reg></choice>` in transcription `p@heb`. The separately selected `transcription_segmented` edition line 134 covers the original token `<orig xml:id="bshe0157-6" xml:lang="arc">אבידתה</orig>`, **not** editorial `reg`. Existing audit #93 reports uncovered canonical signs `bshe0157#s29..s31`. A source word on the orig sibling **must not** relabel the normalized reg signs. `idum0375` drift spans remain separate issue #92.

The complete source-backed #93 inventory is **1,786 uncovered signs**: **1,607** with no segmented edition, and **179** with selected projected words that do not cover the sign. Other residual categories untouched. Exact baseline: 5,535 Brown records, 1,466,387 signs, corrected 35,434, remaining 9,728. All counts must be validated from *executed* new report, never derived from examples.

## Design: additive read-only editorial ownership audit

Inspect **only** `no_selected_word` signs whose source candidate status is `selected_words_do_not_cover_sign`. Use canonical immutable `IRSign.reading_role` (`source`/`normalized`/`both`) and `IRNode.MARKUP` parent edges + `kind` + sign span. Classify by reading role and nearest source branch `orig/reg/sic/corr/lem/rdg` (or `none`), with deterministic disjoint reason counts. For a branch inside `choice` or `apparatus` and a different sibling branch containing a source-selected `WORD`, mark `alternate_branch_has_projected_word`. Require strict shared parent and distinct branch keys; a word elsewhere in the paragraph **does not** count. Do not use text equality or Unicode script to infer language. Store bounded examples with record/key/glyph, role, branch, container, and a source token ID of the covered sibling (not arbitrary paragraph tokens), and top-10 records. Preserve #93's existing no-selected-word inventory unchanged and require `sum(role_counts)=sum(branch_counts)=selected_words_do_not_cover_sign`, plus strict extra histogram for sibling coverage.

Tests first: synthetic canonical IR for (1) choice orig selected word / reg uncovered, (2) apparatus lem selected word / rdg uncovered, (3) uncovered source role, (4) uncovered unmarked sign, (5) projected word elsewhere in paragraph must not count, (6) deterministic bounded examples, invalid role/markup ownership fail-closed if relevant, (7) real EpiDoc parser fixture using `orig/reg` and selected orig word, preserving sign language, source provenance, glyphs/slots. Pre-implementation RED CI; only claim executed failure if actual semantic tests ran.

Pinned gate on exact authenticated 5,535-record parse/reproducible TF checks **actual** role/markup partition of 179, plus pinned `bshe0157` canary and no changed 35,434 correction/9,728 residual, 165 TF features, native app/browser/taxonomy, Ruff, strict MyPy and pytest. Review after final full data. Independent adversarial review must inspect real original source and reject extrapolating sibling orig language to reg.

No parser, resolver, TF graph, schema, Unicode, or source file changes in this PR; it **does not** close #94 or #92 unless evidence is sufficient. If data reveals a safe follow-on, create a separate ticket and separate research-plan-RED-TDD gate.
