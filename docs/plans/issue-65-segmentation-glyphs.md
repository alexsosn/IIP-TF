# Issue #65 — deduplicate segmentation-projected glyph browser notes

## Source and architecture research

Actual pinned Brown `bshe0146.xml` has authored primary transcription
`<g ref="cross"/>` and a corresponding `transcription_segmented`
`<g/>`. Native Text-Fabric has *two* glyph markup nodes over the same
canonical `synthetic_kind=glyph_ref` sign, but projected nodes have
`annotation_source=transcription_segmented`. This is legitimate
source/segmentation alignment proven in #58 / PR #71.

Current `app/app.py::_sign_annotations` iterates all upward `markup`
nodes; whenever `kind=glyph` on a `glyph_ref` sign, it emits a badge.
It does not filter `annotation_source`, so source glyph and segmented
glyph can each make a visible badge on one sign, misleading researchers.

## Research → plan → RED → GREEN → full test → independent review

1. RED native EpiDoc→IR→TF fixture with one `<g ref=cross/>` sign and
   an explicitly segmentation-provenanced markup node attached to its
   same native slot. Through the **real** Flask `/passage` browser,
   require one `glyph ref=cross` badge and no bare duplicate; show
   both original source and segmented TF `markup` nodes still exist.
   Controls: two independent authored glyph signs (two badges), and
   ordinary Unicode source text unaltered.
2. GREEN modify **only browser badge projection**, skipping a glyph
   markup if its native `annotation_source=transcription_segmented`.
   Do not delete nodes, edges or raw refs; do not change format
   selection, converter/writer, critical gap/supply display or
   `T.text`.
3. Add actual pinned Brown `bshe0146` native app smoke to reuse the
   already-loaded full corpus; ensure one visible badge on each source
   glyph sign, without an invented or duplicate segmented badge.
4. Full exact-head Ruff/MyPy/pytest and authenticated native two-build
   + app smoke. Skeptical independent code/data-grounded PR review,
   merge only when all green.
5. This is a narrow #65 visibility correctness slice: the umbrella
   remains open for complete span boundaries, non-primary display
   and richer critical apparatus.
