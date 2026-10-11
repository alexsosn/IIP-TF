# Issue #92-A — audit unaligned Hebrew-encoded Aramaic signs (research gate)

## Authentic source findings

Brown `iip-texts` pinned revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5` and full native verified source tree SHA `4445c4878873227c73ead5e8b94f9e3487c28c3b`. Previous independent double-compiled 5,535-record native TF report (PR #91) gave 45,162 Aramaic transcription effective/script-like `heb` signs at baseline: 35,434 corrected by actual clean `w@arc`, and 9,728 residual. Of the residual, 1,786 are *Hebrew alphabetic signs without a selected projected word covering the sign key*, and two overlap only a source-drifted word. The other 7,940 are synthetic slots, nonletters, other scripts, and unsupported source scopes, and are OUT OF SCOPE for this audit.

Source checks: `anun0005.xml` blob `c1b69cdd5d627fa8e89a25da99436d39dd6fdc0a` has `mainLang=arc`, `div@xml:lang=heb`, transcription `ישראל` and **no transcription_segmented div at all** (not merely a missing token). Do not infer Aramaic from the header or Hebrew Unicode. `idum0375.xml` blob `200afa37eb5fde99991fe4e6998dfcc2986465fd` has `div@heb`, `w@arc` and `<choice><unclear>ען</unclear><unclear>עו</unclear></choice>` in main transcription, versus selected segmented `w@arc` with `<app><lem>נ</lem><rdg>ו</rdg></app>`: two remaining drifted signs, not safe evidence. `jaff0103.xml` blob `6078cb3f19862166bcf74df53866289c918e65ce` has real embedded `foreign@xml:lang=heb` and must remain unchanged.

Existing `segmentation_projection.enrich_segmentation` already records `NodeType.SEGMENTATION` with `selected` (0/1), `token_count`, `resolution_status`, `candidate_index`, and aligned `NodeType.WORD` with `segmentation_status`, `word_text` and `source_id`. Missing candidate means no `SEGMENTATION` nodes. No need to reparse source XML or consult suppressed candidates to know the *selected* state; suppressed candidate evidence cannot authorize text relabeling.

## Bounded plan, not a correction

Implement a **read-only mutually exclusive inventory** of the exact `no_selected_word=1786` population from post-resolution canonical IR inside `AramaicLanguageAudit`, distinguishing:

1. `no_segmented_edition`: zero candidate nodes.
2. `no_selected_candidate`: candidates exist but all unselected (e.g., all empty).
3. `selected_zero_tokens`: exactly one selected candidate, `token_count=0`.
4. `selected_tokens_without_projected_words`: a selected candidate with positive source tokens but no projected `WORD` nodes in the IR.
5. `selected_words_do_not_cover_sign`: selected candidate with at least one projected `WORD` but none covers this canonical sign key.

Precedence above avoids double counting. Candidate selected 0/1 and token_count must be well typed, duplicate selected candidates fail closed. Histograms: reason counts, per-reason bounded examples with real sign/record and selected candidate status, top 10 affected records. For the separate `drift_or_uncertain_word_overlap` population add **bounded** evidence: sign record/glyph/key plus projected word `source_id`, status, language, `source_key` to trace the ambiguity, never count these signs as unaligned.

### Gates

1. Commit **RED unit tests first** for each bucket using canonical IR SEGMENTATION and WORD nodes, duplicate/invalid selected candidate states, non-Aramaic and non-primary-layer controls, deterministic 3-example bound and counts. Add synthetic actual XML→IR parser fixture showing no segmented edition vs segmented covered words. Attempt RED CI before implementation; document if canceled/static analysis intercepts semantic test.
2. Implement additive read-only audit and integrate only into the pinned native **success** JSON via existing `aramaic_transcription_language_audit`, preserving reporting and one-record synthetic failure-ledger behavior. Gate authenticated full pinned `no_selected_word == sum(inventory reasons) == 1786`, drift count == 2, source grounded record example `anun0005`; no invented exact per-reason counts.
3. Ruff, strict MyPy, all pytest, six authenticated Brown source preflight, entire pinned 5,535-record native double parse/build/load and hash equality, Flask app/browser/taxonomy, textual IR as triggered.
4. New independent adversarial review of complete patch and original pinned Brown source; falsify source/selection provenance, missing/duplicate nodes, sample nondeterminism, sum reconciliation and possibility of mistaken linguistic inference. Only merge if exact-head green; no corpus conversion or TF feature changes, no claim #92 fully closed before direct drift resolution research.

Later correction tickets, if source evidence permits, require a new research-plan-RED-TDD gate and their own independent adversarial review. Umbrella #54 remains open.
