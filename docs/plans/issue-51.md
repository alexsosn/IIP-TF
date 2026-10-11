# Issue #51 — make existing non-primary textparts readable in the TF browser

## Real-source research and constraint

Brown IIP `haif0003` has a primary transcription and a non-primary
diplomatic textpart (e.g. `ΜΝΗΣΘΗ`). `bloy0002` has non-primary
translation. The frozen Text-Fabric `fmt:text-orig-full` selects ONLY
an inscription's primary normalized reading, so `T.text` on those
non-primary lines is faithfully `''`: they are not missing data.

Changing the *core* default silently would break existing clients and
their primary-reading contract. Setting the browser default to literal
`text-layer-full` is also unsafe: literal `glyph/after` can expose
BOTH `orig` and `reg` alternatives. But `_add_view_features`
already stores one role-filtered glyph/after pair for each known source
layer (`transcription`, `diplomatic`, `translation`,
`commentary`). Every sign has exactly one layer.

A new **explicit** normalized-by-layer format can concatenate the four
existing glyph/after pairs per slot. It does not create new sign data,
change primary selection, add semantic sidecars or claim that an entire
multi-layer inscription is one unified textual reading. When scoped to
one selected `textpart` or `line`, this gives the appropriate
normalized reading, and is a safe standard browser default.

## Research → plan → RED TDD → implement → CI → skeptical review

1. RED real EpiDoc→IR→TF tests for a single inscription with primary
   transcription `A<choice><orig>X</orig><reg>Y</reg></choice>B`,
   secondary diplomatic Greek, and English translation. The new
   `text-section-normalized-full` must return `AYB` for primary,
   accurate secondary readings for their own sections, **not** `AXYB`;
   legacy `text-orig-full` must remain empty on secondary sections.
2. RED real Flask TF browser `/passage` tests with each textpart,
   proving the default app format is normalized-per-layer and its sign
   renderer actually honors the effective app default when
   `options.fmt=None`. Retain source/editorial overlays for ordinary
   and reference-only sign notes, escaping/RTL and closing scopes (#77).
3. GREEN additive `fmt:text-section-normalized-full` in native
   `_otext()` and 0.1 schema/reference. Change only standard
   `app/config.yaml` default and the sign renderer's effective-format
   selection. Adapt annotation eligibility and after-space formatting,
   without altering core `T.defaultFormat` or sign features.
4. Pinned acceptance against real `haif0003` diplomatic and
   `bloy0002` translation: `text-orig-full` stays empty there,
   explicit normalized-per-layer text and standard `/passage`
   are visible, while primary `abil0001`, `caes0260`,
   `bshe0146` preserve app critical labels, and empty glyph refs
   are still queryable via `text-orig-refs-full`.
5. Exact-head Ruff/MyPy/pytest, six authenticated source canaries,
   complete 5,535-record double-build/reproducibility/browser CI,
   independent adversarial source/code review before merge.
6. This is a bounded browser/explicit-format slice of #51; the
   external Context-Fabric MCP `get_passages` default is **not**
   changed here. Keep #51 open for its end-to-end consumer contract.
