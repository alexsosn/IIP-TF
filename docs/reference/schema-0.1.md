# IIP-TF schema 0.1 reference

This is the researcher-facing summary of `schema/iip-tf-0.1.json`.

## Warp

Slot type: **`sign`**. Native text layers are transcription, diplomatic, translation, and
commentary. `transcription_segmented` supplies validated word boundaries/provenance and is not
a duplicated text layer.

Visible slots hold one Unicode code point. Source-critical zero-width events use one synthetic
sign slot with no fabricated glyph.

## Node types

| Type | Meaning |
|---|---|
| `inscription` | One IIP record and top section |
| `edition` | One transcription/diplomatic/translation/commentary layer |
| `textpart` | Explicit or implicit layer-aware section part |
| `line` | Source line |
| `word` | Validated IIP segmented token projected to primary text |
| `markup` | Structured inline EpiDoc/editorial span or point |
| `entity` | Named/reference span in textual layers |
| `segmentation` | Segmentation provenance/resolution record |
| `bibl` | Bibliographic source entry |
| `hand` | Writing technique / letter dimensions |
| `decoration` | Decoration record |
| `image` | Facsimile URL/credit metadata, never image bytes |
| `revision` | Source revision-history entry |

## Primary text

Selection order: normalized transcription -> diplomatic -> empty anchor.

Translation/commentary never masquerade as source text. Segmented transcription is not a
primary fallback. Missing validated segmentation means no guessed `word` nodes.

## Sections

`sectionTypes=inscription,textpart,line`

`sectionFeatures=inscription_id,section_part,line_n`

`section_part` is layer-aware and incorporates explicit source subtype/n information where
needed for uniqueness.

## Text formats

| Format | Use |
|---|---|
| `text-orig-full` | Default primary text |
| `text-source-full` | Source-oriented primary reading |
| `text-layer-full` | Literal view of one edition/textpart/line |
| `text-transcription-full` | Normalized transcription layer |
| `text-diplomatic-full` | Diplomatic layer |
| `text-translation-full` | Translation layer |
| `text-commentary-full` | Commentary layer |
| `word-default` | Word-node display |

The default uses `primary_glyph` / `primary_after`, undefined on non-primary slots.

## Slot features

Core features include `glyph`, `after`, `layer`, `lang`, `lang_source`, `reading_role`,
`synthetic_kind`, primary/source display pairs, and layer-specific glyph/after pairs.

`synthetic_kind` covers anchor, line/column break, gap, space, hand shift, milestone,
glyph reference, figure, and other audited point events.

## Common node features

All source nodes use `source_id` when `xml:id` exists, otherwise deterministic `source_key`.
Editorial fields include kind/layer/language, reason, certainty, unit, quantity, extent,
bounds, precision, ref, value, rend, type, place, evidence, break, and hand reference.

Raw source values remain available when a typed/derived value is also supplied.

## Markup kinds

The frozen vocabulary includes `supplied`, `unclear`, `gap`, `choice`, `sic`, `corr`, `orig`,
`reg`, `expan`, `abbr`, `ex`, `am`, `del`, `surplus`, `space`, `glyph`, `num`, `foreign`,
`hi`, `hand_shift`, `line_break`, `column_break`, `milestone`, `apparatus`, `lemma`,
`reading`, `add`, `subst`, and `figure`.

Nested markup uses the `parent` edge. Unsupported textual constructs block release instead of
falling into a raw XML/JSON blob.

## Words

`word` features include `token_kind` (`w`, `num`, `orig`), token id, language, word text, and
segmentation status/provenance. Words link to a `segmentation` node through `token_from`.

## Inscription metadata

Scalar record features include unique file-stem `inscription_id`, raw (non-unique) `iip_id` and
`xml_id`, `source_file`, `primary_layer`, language declarations,
genre/religion, object/material/condition, layout, dimensions, origin date/place, Pleiades/
PeriodO references, coordinates, locus, provenance, and physical/origin notes.

## Repeatable metadata nodes

- `bibl`: target, pointer type, scope/unit/n.
- `hand`: technique, note, letter dimensions.
- `decoration`: type, description, locus.
- `image`: URL, description, note, credit/role; no binary payload.
- `revision`: when/custom-when, who, description.

## Entity nodes

`persName`, `name`, `rs`, `placeName`, and textual `date` annotations become `entity` nodes
with ref/ana/nymRef/type/role/language/calendar/from/to fields as applicable.

## Edges

| Edge | Meaning |
|---|---|
| `parent` | Immediate nested semantic parent |
| `in_inscription` | Explicit owner for technically anchored metadata/provenance |
| `corresponds_to` | Resolved local EpiDoc `@corresp` |
| `cites` | Relation to bibliography |
| `segmentation_of` | Segmentation provenance annotates an edition |
| `token_from` | Word derives from selected segmentation |

## Empty and zero-width material

One zero-width source event consumes one synthetic sign regardless of encoded quantity.
Metadata reuses the first primary anchor where possible; only an inscription with no primary
source slot gets a technical anchor. Empty editions are retained without invented lines.

## Record identity

`inscription_id` is the repository filename stem and is the top TF section key. It is used
because the pinned source contains duplicated IIP ids and duplicated TEI `xml:id` values
across different files.

`iip_id` and `xml_id` remain verbatim source metadata. Source element ids are scoped by
source file. Bare local `@corresp` resolves within that file only; cross-file resolution
requires an explicit file-qualified target.

## Provenance and licensing

Source pin: `Brown-University-Library/iip-texts@0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.
DOI: `10.26300/pz1d-st89`. Generated IIP-derived data carry project CC BY-NC 4.0 terms;
IIP-TF converter software is MIT. Bibliography remains queryable. Image binaries are outside
the corpus unless separately licensed.

## Compatibility

Shared semantics use familiar `sign`, `word`, `line`, `lang`, `glyph`, `after`, normal TF
sections/formats/search/API/app workflow. Lexeme, clause, phrase, and morphology features are
not created unless the source actually supplies such analysis.

## Failure policy

Unsupported textual constructs, duplicate canonical/file-scoped identity, unresolved segmentation conflicts,
non-deterministic token projection, and malformed records lacking an explicit researched
policy are release-blocking. Silent source-data loss is forbidden.