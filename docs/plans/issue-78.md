# Issue #78 — retain source ownership of normalized inline spaces

## Research
In the EpiDoc parser, _emit_text() collapses horizontal whitespace into the
preceding sign's after string. The inline _parse_inline() creates markup nodes
before the enclosing parent processes child.tail, so an inner trailing space is
still distinguishable at that precise boundary. The two examples
A<supplied>BC </supplied>D and A<supplied>BC</supplied> D produce identical
text and sign slots but different source owners for the blank.

Six pinned Brown XML canary files were sampled. No direct horizontal-space
examples at supplied/unclear/abbr/ex boundaries were identified in that
small sample. This is NOT a whole-Brown corpus frequency finding.

## Architecture
Record a sparse **native MARKUP node feature**
source_trailing_space_inside="yes" when the last sign in an inline
element already has after=" " *before* processing that element's tail.
Never write this to arbitrary metadata sidecars or add whitespace slots.
It encodes one existing normalized space's XML boundary ownership, NOT
exact original whitespace bytes, indentation, or unmodelled punctuation.
Keep existing IR sign glyph/after, sections, otext formats, and default
Text-Fabric source readings byte-for-byte stable.

For editorial closing badges, partition nested markup into closes before
the existing after-space (no inside marker) and closes after it
(source_trailing_space_inside=yes). Preserve inner-before-outer order.
When there is no actual after-space, keep all closes after the sign.
Ensure RTL/HTML escaping remains unaffected.

## TDD → GREEN → complete corpus → independent review
1. RED paired inside/outside real EpiDoc→IR→TF fixtures: identical plain
   readings, distinct source_trailing_space_inside feature.
2. RED real TF browser Flask /passage: the close marker must appear after
   the space when inside and before when outside. Include nested spans
   with mixed inside/outside ownership, two editorial types, escaped
   source text and a line-break control.
3. GREEN parser + minimal browser hook only. Explicitly document that
   this does NOT recover exact source spaces, multiple whitespace,
   alternative reading ambiguity or all TEI constructs.
4. Verify raw source/TF serialization, exact-head Ruff/MyPy/pytest,
   authenticated six-source preflight, complete pinned 5,535-inscription
   double-build/reproducibility, full browser smoke, failure reports.
5. Conduct logically separate adversarial code/data review of the final
   exact tested head; keep issue #78 open if wider whitespace cases
   remain unrepresented.
