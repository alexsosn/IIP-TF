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
| `paragraph` | Source textual block (`p` or textual `ab`), including block-level language/certainty |
| `line` | Source line |
| `word` | Validated IIP segmented token projected to primary text |
| `markup` | Structured inline EpiDoc/editorial span or point |
| `entity` | Named/reference span in textual layers |
| `segmentation` | Segmentation provenance/resolution record |
| `bibl` | Bibliographic source entry |
| `bibl_scope` | Repeatable `biblScope` child |
| `hand` | Writing technique record |
| `dimension` | Repeatable physical or letter-dimension record |
| `support_note` | One non-empty direct `support/p` physical-support note |
| `decoration` | Decoration record |
| `facsimile_surface` | Source facsimile surface/caption grouping |
| `image` | Graphic URL/credit metadata, never image bytes |
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
| `text-layer-full` | Literal stored-slot view of one edition/textpart/line; may expose both editorial branches |
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

## Textual blocks

Source `p` and textual `ab` elements become `paragraph` nodes. They preserve block order,
`xml:lang`, `cert`, and multiple paragraphs inside one edition. Paragraphs do not change the
three-level TF section hierarchy.

## Feature value types

Each TF feature has one serializable value type. Raw source attributes are strings. Numeric
derivatives use separate features only when lossless, for example:

- `quantity` (str) and optional `quantity_int` (int);
- `date_not_before` (str) and optional `date_not_before_int` (int);
- `date_not_after` (str) and optional `date_not_after_int` (int).

`candidate_index`, `selected`, `token_count`, and writer-derived `point_index` are also integer features.

No feature is int-or-string depending on the node.

## Words

`word` features include `token_kind` (`w`, `num`, `orig`), token id, language, word text, and
segmentation status/provenance. Words link to a `segmentation` node through `token_from`.

Inline markup from the selected segmented candidate is not discarded and does not create a
second copy of text. It becomes markup annotations on the deterministically projected primary
slots with `annotation_source=transcription_segmented`. This includes the audited
`app/lem/rdg` case.

## Inscription metadata

Scalar record features include unique file-stem `inscription_id`, raw (non-unique) `iip_id` and
`xml_id`, `source_file`, `primary_layer`, language declarations, genre/religion,
object/material/condition, layout, origin date/place, Pleiades/PeriodO references,
coordinates, locus, provenance, and scalar condition/layout/origin notes. Repeatable physical
support paragraphs are not collapsed into an inscription scalar.

`genre_cert`, `date_precision`, `region_cert`, and `settlement_cert` preserve audited raw
certainty/precision qualifiers for their specific metadata paths rather than sharing a generic
`cert` scalar.

## Repeatable metadata nodes

- `bibl`: target and pointer type.
- `bibl_scope`: one repeatable scope child with text/unit/n.
- `hand`: technique and note; child `dimension` nodes hold letter dimensions.
- `dimension`: raw string-valued surface/letter dimensions including axis-specific min/max ranges.
- `support_note`: one `support_note` node per non-empty direct `support/p`, preserving repeated source paragraphs independently.
- `decoration`: type, description, locus.
- `facsimile_surface`: shared surface description/note context; nested `facsimile_surface` nodes preserve source surface hierarchy.
- `image`: URL, description, note, credit/role; parented to a surface when present; no binary payload.
- `revision`: when/custom-when, who, description.

## Source responsibility and publication provenance

The pinned 5,535-record source audit (`docs/research/issue-49-responsibilities.md`)
justifies the following additional native node types:

- `responsibility`: one `titleStmt/respStmt` or exceptional
  `titleStmt/principal`; preserves raw `responsibility_role`, construct,
  agent tag (`name` versus `persName`), agent name and local
  `agent_source_id`. It never implies global person identity.
- `publication_id`: one `publicationStmt/idno`, including empty elements.
- `publication_include`: one **unexpanded** XInclude pointer, literal
  `include_href`, fallback diagnostic and `include_resolved="0"`;
  neither publisher nor licence is inferred from external content.
- `publication_availability`, `publication_licence`,
  `publication_paragraph`, `publication_reference`: preserve source-explicit
  availability and licence text, structural paragraph and reference
  parentage, and original reference targets, without a semantic sidecar.

Every new metadata node has a technical sign anchor plus a direct `parent`
and `in_inscription` edge. Inscription scalar `source_title` stores the raw
TEI title statement text (whitespace-normalized); `publication_authority`
exists only when the original record explicitly provides an authority.

The pinned source has 5,536 `respStmt` plus one `principal`, 5,535 publication
identifiers, 3,483 unexpanded includes, 2,052 explicit authorities, and
three explicit nested licence declarations. The source typo
`Prinicipal Investigator` is deliberately retained.

## Entity nodes

`persName`, `name`, `rs`, `placeName`, and textual `date` annotations become `entity` nodes
with ref/ana/nymRef/type/role/language/calendar/from/to fields as applicable.

## Edges

| Edge | Meaning |
|---|---|
| `parent` | Immediate nested textual or metadata parent (including scope/dimension/surface grouping) |
| `in_inscription` | Explicit owner for technically anchored metadata/provenance |
| `corresponds_to` | Resolved local EpiDoc `@corresp` |
| `cites` | Relation to bibliography |
| `segmentation_of` | Segmentation provenance annotates an edition |
| `token_from` | Word derives from selected segmentation |

## Empty and zero-width material

One source-critical zero-width event consumes one synthetic sign regardless of encoded quantity.
Metadata reuses the first primary anchor where possible; only an inscription with no primary
source slot gets a technical anchor. Empty editions and empty paragraph blocks are retained
without invented text or lines.

Empty inline semantic markup is different from an empty structural container. Its canonical IR
node has no `sign_keys`, but preserves `point_index`: a record-local boundary offset in
`InscriptionIR.signs`. Offset 0 is before the first sign; offset `len(signs)` is after the
last; interior offset `k` is between signs `k-1` and `k`. This also applies when selected
segmented markup projects to a zero-width point. Ambiguous point projection fails closed.

`point_index` is an IR semantic coordinate, not another text layer or slot. The native TF
writer gives an empty inline `markup` or `entity` node one adjacent technical `oslots` anchor,
preserves `point_index` as an integer TF feature, and writes
`point_relation=before|after` so the boundary is independently reconstructable from the anchor.
Empty structural nodes use the existing
inscription-anchor policy and do not acquire point semantics.

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

## Cardinality guarantee

Repeatable source children remain repeatable TF nodes. The converter must report a schema error rather than overwrite/concatenate repeated values that the frozen mapping treats as scalar.


## Source EpiDoc mapping coverage

`schema/iip-tf-0.1.json` contains an explicit mapping for every element and attribute observed
in the audited textual contexts. CI checks the mapping against the pinned `iip-inventory.json`.

Examples:

- `p` / textual `ab` -> `paragraph`;
- `w` -> `word`;
- `app`, `lem`, `rdg` -> apparatus/lemma/reading markup annotations;
- `figure` -> figure markup, with `figDesc` as its description rather than visible text;
- rare textual `height` -> `markup(kind=height)`;
- `persName`, `name`, `rs`, `placeName`, textual `date` -> entity nodes;
- `gap@quantity` -> raw string `quantity` plus optional lossless `quantity_int`;
- `p@xml:lang` -> paragraph `lang`.

A source element/attribute missing from the frozen mapping is a schema error, not a silent drop.
