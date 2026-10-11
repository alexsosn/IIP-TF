# #54-D research gate — audit remaining script-like `heb` labels

## Verified baseline, 2026-10-11

PR #87 (squash `f42bb825d58cc6f3f72715a01aa780d2a6eee774`) corrected 5,159 Aramaic transcription signs from selected drift-free `w@xml:lang=arc` evidence; native pinned report authenticated 5,535 Brown records, 1,466,387 signs, two reproducible builds, source tree SHA `4445c4878873227c73ead5e8b94f9e3487c28c3b`. Original issue #54 reported 45,162 Aramaic-record transcription signs with `lang=heb` BEFORE correction, but that baseline includes characters that are not necessarily eligible for language repair. Do **not** subtract 5,159 and assert all remaining signs are mistranscribed: first obtain a like-for-like post-PR inventory with explicit status/provenance and coverage.

Source-backed canaries at Brown pin `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`: `chor0001` original blob `f08f433383d889b6afaaf31f93edf1f725b0a9d8` has Aramaic main language, `p@xml:lang=heb` and `w@xml:lang=arc` in segmented source. `beth0023` blob `1bd3522dc5b6c3d0ac8f4869f8693dcabd541888` has explicit `foreign@arc-Grek`, so encoded script and language are orthogonal. `sina0114` blob `28a159b5290d0f77e9ea37c4c7c23cd1234f0e51` is Latin transliteration and segmented `Other`, not a reason to guess historical script or language. Inline name `caes0044` `persName@xml:lang="egy "` is separate issue #55.

## Plan & explicit non-goal

**Research-only slice:** produce a deterministic, mutually exclusive **language-coverage audit** from the **post-resolution canonical IR** and the *selected word nodes already projected onto native sign keys*. Count the exact post-#87 `main_lang=arc`, `layer=transcription`, effective `lang=heb` sign population; also count the independently evidenced corrected signs. For each residual sign classify by source declaration/origin, actual encoded glyph (synthetic, punctuation, other letter, Hebrew letter), segmented evidence (none, drift or uncertain, clean non-`arc`, missing language, unexpected still `arc`). Preserve bounded **record ID, sign key, glyph** examples per category, deterministic top affected records, and full arithmetic reconciliation (sum of reason buckets == residual). Avoid scan of all 5,535 records for multiple copies and do not add TF features or change `lang`.

Semantic limits: a sign labeled `heb` even if `arc` elsewhere might represent a genuine embedded Hebrew word; audit calls it "unresolved" rather than necessarily erroneous. A mismatched/unknown word is evidence *not to infer*. A clean `arc` word over otherwise eligible `heb` signs would violate the earlier gate and should **fail**. A "corrected" sign with no reliable matching `arc` word or with a drift overlap must **fail**. Never silently drop words lacking `xml:lang`.

## RED / GREEN / data / skeptical review

1. Commit RED unit tests for mutual exclusivity, source-origin guards, no guess for `foreign`, drift overlap precedence, word-language conflicts, no-word source, punctuation/synthetics, corrected-sign correspondence, stable bounded examples, and non-Aramaic exclusion. Run CI RED before implementation; mark honestly if test is prevented by imports/lint.
2. Implement audit in a standalone typed module, wire it only into pinned native **successful** report without weakening failure ledger or schema. Report field `aramaic_transcription_language_audit`.
3. Validate Ruff + strict MyPy + pytest; authenticated Brown 5,535 record native double parse/build/reload/reproducibility + browser/taxonomy; pinned textual IR. Observe *actual* per-bucket counts in run logs and document them explicitly; do not guess.
4. Logically independent adversarial review of patch, original Brown records and actual report: seek double counting, missing segmented tokens, memory blow-up, source provenance leaks, false safe classification, report output nondeterminism, corrupted failure reports. Refuse merge until exact-head gates fully green.

After the inventory, revisit #54 for explicit signed-off rules; #55 and #52 remain separate.
