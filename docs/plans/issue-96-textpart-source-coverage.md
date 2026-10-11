# Issue #96-A — Source textpart scope among 168 non-editorial uncovered signs

## Research

PR #95 source-verified result on Brown `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5` (complete original source tree `4445c4878873227c73ead5e8b94f9e3487c28c3b`): 179 signs in Aramaic transcription have a selected segmented edition yet no covering selected source WORD; **11** are normalized `reg` under an `orig` with projected word, **168** have `markup_branch=none`. Counts by `reading_role`: `both=167,normalized=12`, so there is exactly one normalized sign outside recognized editorial `reg` branches. Do not infer language from this discrepancy.

Original, independently inspected pinned Brown EpiDoc:
- `mare0134.xml`, blob `51d20dff2090780fa023b94b5f1cf661b554cd15`, primary textpart columns `a`, `b`, `bottom-line`, `left-margin-lines`; selected segmented source only six words matching column a. Actual 62 uncovered; diagnostic must distinguish other textparts from genuine missing coverage inside annotated textpart.
- `zoor0414.xml`, blob `fc17b18b44d361894f9e1a47fea63de63ac9f621`, two explicit source textparts, source `mainLang=arc,otherLangs=he`; selected segmented has word and `num` tokens. Actual 39 uncovered; word absence is not proof of source-language identity.
- `idum0490.xml`, blob `90349b1b37e1d68880583266be8e1aca84afa9ce`, source `div@heb`, segmented `w@arc` plus `num`; actual 7 uncovered.

Canonical `TEXT_PART` node type is `NodeType.TEXTPART` (not `TEXT_PART`), feature `section_part` recorded by parser, e.g. `transcription:column:a`. The implicit fallback is `transcription`. Selected projected source tokens all use `NodeType.WORD` with `token_kind=w/orig/num...`, `candidate_index`, `segmentation_status=projected`.

## Bounded read-only implementation

Only for signs already classified by merged #95 as `selected_words_do_not_cover_sign` and `markup_branch=none`: count disjoint textpart source scopes `explicit_with_selected_word`, `explicit_without_selected_word`, `implicit_with_selected_word`, `implicit_without_selected_word`, `no_textpart`. A projected word in another textpart is **not** evidence in this textpart; only selected candidate index and exact canonical sign-key overlap with a textpart count. Count both ordinary `w` and non-`w` token types as source token kinds, but preserve a separate per-kind histogram, no numeric glyph/language inference. For the normalized non-`reg` outlier, report its exact record, sign key, glyph, `section_part`, and source provenance (bounded). Store deterministic bounded representative examples per category, top records, and sum invariants `168 = sum(scope_counts)` and 11 editorial reg signs excluded; keep sign-language report unchanged.

## Gates

Commit RED-first canonical IR/real EpiDoc tests before implementation: multiple textparts, selected token in different textpart does not count, word in same textpart, implicit part, source `num` projected token, normalized `supplied` outside editorial `reg`, duplicated textpart ownership false safety, and deterministic sample bounds. Exact head CI Ruff, strict MyPy, pytest, real Brown six-canary, 5,535-record native double parse/build/reload and byte reproducibility, app/browser/taxonomy. Independently source-grounded adversarial review on exact final head before squash merge. No `IRSign`, `IRNode`, `IREdge`, glyph, language, Unicode, schema, source or TF output modifications.

#96 can remain open if unexplained source-level cases remain. Parent #92/#54 remain open.
