# Issue #65 — preserve editorial annotations in opt-in source-ref view

## Research

PR #71 added source-faithful opt-in native TF `text-orig-refs-full`,
whose template is `{primary_glyph}{primary_ref_token}{primary_after}`.
It has *exactly the same* primary normalized-layer and `reading_role`
selection as `text-orig-full`; only otherwise-empty authored
`<g ref>` events acquire explicit `((ref))` **display labels**. The
source `glyph`, `primary_glyph`, markup nodes, and default original
reading stay unchanged.

Current standard browser custom renderer `app/app.py` uses
`_is_selected_sign` to prevent unrelated layer/choice apparatus
from leaking into the displayed view. It recognizes `text-orig-full`
and `text-source-full` but not `text-orig-refs-full`, treating that
registered format as 'unknown' and suppressing ALL editorial badges.
This is a browser presentation regression: explicit ref tokens make
a source ID readable but lose source-critical gap/supply/unclear and
glyph metadata. The underlying native TF feature data remains intact.

## Research → plan → RED TDD → implement → test → review

1. RED: small real EpiDoc→IR→native TF fixture with primary
   transcription source `<g ref>`, `<supplied reason=lost>`, gap,
   translation/diplomatic control, and a normalized-vs-source
   alternative. Exercise the actual app's sign renderer, not only
   string matching of the code. Require the opt-in format to retain
   the identical primary normalized apparatus selection as
   `text-orig-full`, and preserve honest `text-source-full`
   selection. Also verify no source chars are fabricated and
   `T.text` remains unchanged.
2. GREEN: explicitly recognize the opt-in format as a **primary
   normalized reading** in `_is_selected_sign`; do not add
   unrelated alias/fallback guesses. No TF writer/source changes.
3. Fix stale researcher browser-guide language from before #71:
   `text-orig-full` remains empty on source-ref-only
   inscriptions, but opt-in `text-orig-refs-full` is now supported.
   Clearly distinguish optional reference labels vs actual source
   Unicode glyphs; do not advertise upstream conversion as
   published in a one-command TF install.
4. Add pinned app/real Brown `masa0286` and `abil0001`
   selected-format smoke using already loaded authenticated TF.
   Keep existing full TF/browser/build reproducibility gates.
5. Exact-head CI, six-file canary and authenticated double-build
   with independent adversarial review before merge. Keep broader
   #65 and #58 open for span/other-layer work.
