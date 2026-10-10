# Issue #65 — browser-visible source-critical editorial apparatus

## Research: source and TF implementation

Pinned Brown XML `abil0001` contains `<supplied reason="lost">`,
`<gap reason="lost" unit="character" extent="unknown"/>`, and
`<unclear>`; `caes0260` has `<abbr>/<ex>`; `masa0286`
contains empty `<g ref="phoen-gaml"/>` points. The converter models
these in *native TF* `markup` nodes and technical `sign` slots,
which ordinary `text-orig-full` leaves nontextual/invisible.

In TF 13.1 `tf.advanced.render._render`, a `plainCustom` hook for a
non-slot line suppresses the line's entire child traversal and risks
deleting ordinary characters. The safer precedent is in the project's
sibling [TLHdig-TF](https://github.com/alexsosn/TLHdig-TF/blob/main/app/app.py):
bind a sign-level `plainCustom` in a `TfApp` subclass, render
`app.api.T.text(sign, fmt=options.fmt)` *without altering the source
reading*, escape all raw data, and add presentational classes/markers
from native TF features. Avoid a second browser or semantic sidecar.

## Plan / gates

1. RED real-TEI -> IR -> TF + real Flask `/passage` fixtures, including
   supplied text with low certainty, unknown-extent zero-width gap,
   `unclear` text, glyph-reference-only reading, ordinary unannotated
   text, and an HTML-escaping negative case.
2. GREEN source-derived render annotations at each sign using its parent
   `markup` nodes only. Highlight `supplied` and `unclear` with a
   visible label and optional title, emit a distinct bracketed label for
   an empty `gap` or `glyph_ref` technical sign, and never replace
   source characters with invented readings. Do not turn English badge
   text into part of `T.text`. Limit visible annotations to signs
   relevant to selected display layer, using actual corpus `layer`.
3. Preserve TF's requested format, escape both text and metadata,
   avoid double-counting nested markup, and ensure plain uncomplicated
   inscription remains legible.
4. Add a real pinned browser smoke on `abil0001`, `masa0286`,
   `caes0260`, and `chor0001`, reusing the already-loaded corpus.
   Recognize native `text-orig-full` cannot display nonprimary
   textparts (#51).
5. Exact-head ordinary CI and 5,535-record full pinned build,
   logically independent skeptical code/data review, merge only
   after both green. #65 remains open if wider nested apparatus and
   complex nonprimary display is not fully covered. No sidecars.

Caveat: sign-level annotations describe **editorial evidence**;
copying/transcribing those labels is not the same as source text.
