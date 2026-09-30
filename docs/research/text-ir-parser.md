# Research — canonical textual IR and EpiDoc parser

Issue: #24, child of #4.

## Frozen inputs

The parser implements schema 0.1 from `schema/iip-tf-0.1.json`. It does not invent a
second schema in code.

Input first passes through the #15 source-repair preflight. The textual parser then handles
the four native layers:

- `edition/transcription`
- `edition/diplomatic`
- `div type="translation"`
- `div type="commentary"`

`transcription_segmented` is deliberately not parsed as independent text in #24. #26 will
consume it as annotation/provenance and project validated token boundaries onto primary slots.

## IR boundary

The canonical IR must be independent of Text-Fabric serialization while carrying exactly the
information the TF writer needs.

The minimum graph model is:

- `IRSign`: one Unicode code point or one synthetic source position;
- `IRNode`: typed structural/span/metadata node with explicit scalar features;
- `IREdge`: typed semantic relation;
- `IRDiagnostic`: deterministic warning/error evidence;
- `SourceIdentity` and `SourceProvenance`;
- `InscriptionIR`: immutable aggregate with lookup helpers.

IR objects may contain strings, integers, tuples and typed enums. They must not contain raw XML
fragments, generic attribute dictionaries copied wholesale from TEI, or JSON/XML sidecars.

## Deterministic identity

The canonical record key is the source filename stem. Raw TEI `xml:id` and every
`idno[@type="IIP"]` value encountered in the record are preserved as source identity
metadata; they are not assumed globally unique.

Source element keys are file-scoped:

- existing `xml:id`: `<inscription>#id:<xml-id>`;
- no `xml:id`: deterministic structural path
  `<inscription>#path:/TEI[1]/text[1]/body[1]/...`.

Duplicate ids among native textual elements in one file are parser errors. Duplicate ids in
suppressed `transcription_segmented` candidates are outside #24 and are handled by #20/#26.

## Slots and whitespace

Visible text becomes one sign per Unicode code point. Ordinary XML whitespace does not create
slots. A run of source whitespace between visible textual items becomes at most one separator
on the preceding sign. Pretty-print indentation at block boundaries must not leak into text.

Paragraph boundaries are represented structurally and may contribute a rendering newline later;
they are not fake glyphs.

Source `lb` is a real zero-width event. It creates one synthetic sign and one
`markup(kind=line_break)` node. It starts the next `line` section. A leading `lb` starts
line 1 and must not create a useless empty line before it.

Other source-critical zero-width constructs frozen by schema 0.1 — gap, encoded space,
handShift, cb, milestone, empty glyph reference and figure — create exactly one synthetic sign
per event. Quantity never multiplies synthetic slots.

## Reading alternatives

All branches remain in source order in the IR. A sign carries a reading role used later by text
formats:

- `both`: ordinary text, abbreviation body, unclear text;
- `normalized`: corr, reg, ex, supplied;
- `source`: sic, orig, am, del, surplus.

Nested roles combine restrictively. No branch is deleted merely because the default display
will suppress it.

`choice`, `expan`, and related containers are markup nodes with parent edges to their child
markup nodes. Equal spans therefore do not erase hierarchy.

## Language

Effective language follows the nearest explicit `xml:lang`; otherwise it inherits from the
edition/textpart/paragraph context and finally `textLang/@mainLang`. The raw source code is
preserved (after trimming accidental boundary whitespace such as `"grc "`) and
`lang_source` records whether it came from explicit XML language, inheritance, header
main language, or no source.

The parser does not collapse `he`, `heb`, `hbo`, `la`, `lat`, etc.

## Sections

The parser creates:

- one `inscription` node;
- one `edition` node per native source layer, including empty editions;
- explicit `textpart` nodes, or one implicit textpart for a non-empty layer without them;
- `paragraph` nodes for textual `p` / `ab`;
- `line` nodes according to source `lb`.

Empty editions remain nodes but do not acquire invented textparts/lines. The record-level empty
technical anchor is created only when neither transcription nor diplomatic has a non-empty
source-text position.

## Entities

Translation/textual `persName`, `name`, `rs`, `placeName`, and `date` become
`entity` nodes over the same textual signs, retaining their mapped source attributes and
nested parent relation.

## Strictness

The pinned audit enumerates every textual element and attribute observed in the source. #24
must maintain explicit supported element/attribute sets derived from the frozen schema mapping.

An unrecognized textual element or textual attribute raises a deterministic
`UnsupportedTextualConstructError`. Silent dropping is forbidden.

Header/facsimile/bibliography metadata is outside #24 and will be parsed in #25; ignoring those
subtrees at this stage is intentional and explicit rather than a generic skip mechanism.
