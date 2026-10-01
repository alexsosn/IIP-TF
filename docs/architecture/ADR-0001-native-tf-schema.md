# ADR-0001 — Native Text-Fabric schema for IIP-TF 0.1

Status: **Accepted for 0.1**

Issue: #3. Evidence base: #2, #16, #18, #20.

## Decision

IIP-TF 0.1 uses a single `sign` warp. Genuine textual layers are native TF text:
`transcription`, `diplomatic`, `translation`, and `commentary`.

`transcription_segmented` is not copied as a fifth text. It is an annotation/provenance
source for validated `word` nodes whose boundaries are projected onto primary source-text
slots only when the projection is deterministic.

No raw XML or JSON blob is used as an escape hatch for source semantics.

## Primary source text

Primary text is selected per inscription in this order:

1. non-empty normalized transcription;
2. otherwise non-empty diplomatic text;
3. otherwise one empty technical anchor.

#18 found 374 records that need diplomatic fallback. The sole record with segmented text
but no normalized transcription (`masa0779.xml`) also has diplomatic text, so segmented text
never needs to become a competing primary edition. Eighteen parsed records have no non-empty
source-text candidate and receive one `synthetic_kind=anchor` slot with no visible glyph.

There is no whitespace-tokenization fallback and no invented morphology.

## Why all text layers share the warp

Diplomatic text has its own `gap`, `unclear`, `choice`, `space`, glyph, supplied text, and
line structure, and most diplomatic editions have no explicit alignment to normalized
transcription. A string feature would lose ordering and spans. Real sign slots preserve the
layer natively without inventing alignment.

An `inscription` spans all textual slots for the record. `edition`, `textpart`, `paragraph`,
and `line` nodes delimit each layer. Source `<p>` and textual `<ab>` elements become
`paragraph` nodes, so multiple blocks and block-level `xml:lang`/`cert` are not flattened.
Paragraphs are not TF sections; section navigation remains inscription/textpart/line. Default
rendering does not concatenate all layers: only primary
slots get `primary_glyph` / `primary_after`; layer-specific formats render the others.

## Sections

The standard section hierarchy is `inscription -> textpart -> line` with section features
`inscription_id`, `section_part`, and `line_n`. `inscription_id` is the unique repository file
stem, because the source audit found 26 duplicated IIP ids and 9 duplicated TEI `xml:id`
values across different files.

Explicit EpiDoc textparts are preserved. A non-empty layer without explicit textparts gets
one implicit layer textpart. Every source `lb` begins the following line and is also retained
as a structured zero-width event. Empty editions stay as edition nodes but get no invented line nodes. Empty source paragraphs
may be retained as paragraph nodes on the edition's technical anchor without inventing text.

## Signs and zero-width source positions

A visible sign is one Unicode code point. Source-critical zero-width events get exactly one
synthetic sign in source order. This includes line/column breaks, gaps, encoded spaces, hand
shifts, milestones, empty glyph references, and zero-width figures.

`gap quantity=5` still creates one synthetic position, not five fake signs. Quantity, unit,
extent, certainty, and related semantics remain features on the markup node.

Metadata nodes reuse an existing primary anchor. A technical anchor is created only when no
primary source-text slot exists. Metadata ownership is explicit through `in_inscription`;
the oslot anchor is merely a TF technical requirement.

## Editorial markup

Inline EpiDoc is represented by `markup` nodes with an enumerated `kind` and typed scalar
features. The frozen kinds include supplied/unclear/gap, choice branches, expansion and
abbreviation structures, deletion/surplus, spaces, glyphs, numerals, foreign spans, display
markup, hand shifts, line/column breaks, milestones, apparatus/lemma/reading, additions,
substitutions, and figures.

Nested markup uses the `parent` edge, so equal spans do not erase hierarchy. The rare textual
`height` element is preserved as `markup(kind=height)`. `figDesc` is stored as the description
of its enclosing `figure` markup and is not rendered as an inscription glyph. Unknown textual
constructs are release-blocking diagnostics. There is no generic opaque attribute dictionary.

## Alternative readings

All source branches remain queryable; display selection is derived rather than destructive.
Normalized choice rendering selects `corr` over `sic` and `reg` over `orig`; source-oriented
rendering selects `sic` / `orig`. Expanded abbreviations preserve `abbr`, `am`, and `ex`
separately. Supplied, deleted, surplus, unclear, and gap semantics remain structured even when
a format suppresses or styles their visible text.

## Words and segmented transcription

`word` nodes come only from selected, validated IIP segmentation. #20 established the
duplicate resolver: single/sole-nonempty candidates are accepted, complete-subtree-equivalent
reruns collapse, the pinned `zoor0453` anomaly has a narrow source-history override, and
unknown conflicts fail closed.

Projection from selected segmented tokens to primary source text must be deterministic.
Failure is release-blocking; the converter never guesses boundaries.

`segmentation` provenance nodes preserve candidate run dates/resolution. `word` nodes link via
`token_from`; segmentation nodes link to the annotated edition via `segmentation_of`.

Selected segmented markup is also preserved. It does not create a fifth set of sign slots:
inline elements inside the selected `transcription_segmented` candidate are projected onto the
same deterministically matched primary slots as annotation `markup` nodes and carry
`annotation_source=transcription_segmented`. This matters in real source data such as
`idum0375`, where segmented `app/lem/rdg` encodes an alternative differently from the
normalized transcription. If such annotation cannot be projected without guessing, conversion
fails closed.

## Text formats

Frozen low-level formats are `text-orig-full`, `text-source-full`, `text-layer-full`,
`text-transcription-full`, `text-diplomatic-full`, `text-translation-full`,
`text-commentary-full`, and `word-default`.

Layer-specific formats use derived slot features that are undefined outside that layer, which
is ordinary Text-Fabric format behavior. #8 may add normal TF app styling, but no separate web
application is part of the architecture.

## Text-Fabric feature value types

Every emitted TF feature has exactly one `@valueType`. Raw source attributes are preserved as
string features. A numeric convenience feature is separate and emitted only when conversion is
lossless: for example `quantity` (raw string) / `quantity_int` (int), and
`date_not_before` / `date_not_before_int`. This avoids impossible mixed int/string TF
features and preserves spellings such as `unknown` or non-canonical source values.

## Metadata

One-to-one language, classification, origin, and provenance values live on `inscription`.
Audited certainty/precision on those scalar claims remains path-specific: `genre_cert` stores `msItem@cert`, `date_precision` stores origin `date@precision`, `region_cert` stores origin `region@cert`, and `settlement_cert` stores origin `settlement@cert`. These are raw source strings and are not collapsed into the generic textual/editorial `cert` feature.
Repeatable/structured data become native nodes: `bibl`, `bibl_scope`, `hand`,
`dimension`, `support_note`, `decoration`, `facsimile_surface`, `image`, and `revision`.
The pinned corpus contains repeatable support paragraphs in four records, so each non-empty
direct `support/p` is a `support_note` node rather than a delimiter-joined inscription scalar.
Translation/reference spans such as `persName`, `rs`, `name`,
`placeName`, and `date` become structured `entity` nodes.

A `biblScope` is its own repeatable `bibl_scope` child node rather than a scalar on
`bibl`; the pinned audit has more scopes than bibliography entries. Every source
`<dimensions>` becomes a `dimension` node so decimal values, axis-specific ranges, repeated
dimension records, and hand-letter dimensions survive unchanged.

Facsimile `surface` grouping is preserved with `facsimile_surface` nodes. Child graphics
become `image` nodes parented to the surface; graphics directly under `facsimile` belong
directly to the inscription. Nested facsimile surfaces preserve their direct surface parent;
the pinned source has one depth-2 case (`mgha0001`). URLs, descriptions, notes, and credits are kept. Image binaries
are not copied into the corpus because IIP does not establish one uniform redistribution right
for every image.

## Edges

- `parent`: direct nested textual/metadata parent, including markup, paragraph blocks, bibliography scopes, dimensions, and facsimile surface/image grouping;
- `in_inscription`: semantic owner for technically anchored metadata/provenance;
- `corresponds_to`: resolved local EpiDoc `@corresp` relation;
- `cites`: relation to a bibliography node;
- `segmentation_of`: segmentation provenance to annotated edition;
- `token_from`: word to selected segmentation provenance.

Raw source reference strings remain features when an edge is additionally resolved.

## Provenance and rights

Generated TF records Brown IIP as upstream source, exact commit
`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, DOI `10.26300/pz1d-st89`, project CC BY-NC
4.0 terms, converter commit/version, and schema version. Converter software remains MIT.

Bibliography stays queryable for underlying scholarly attribution. Image references/credits
are metadata only unless image rights are separately established.

## Identity

The canonical record key and top section heading is `inscription_id`, the unique source-file
stem. Raw `idno[@type='IIP']` and `TEI/@xml:id` are both preserved verbatim as `iip_id` and
`xml_id`, but neither is assumed globally unique.

Source element `xml:id` values are file-scoped. Nodes without one get a deterministic
file-scoped `source_key`. Bare local `@corresp` references resolve only inside their source
file; a cross-file edge requires an explicit file-qualified target. A derived value never
overwrites the raw source value. Duplicate canonical file keys or duplicate element ids
within one file are release-blocking; cross-file raw-id collisions are preserved and reported.

## Representative cases

- Greek transcription: visible signs plus `markup(kind=supplied)` and projected IIP `word` nodes.
- Mixed Hebrew/Aramaic: source language codes remain distinct and `lang_source` records provenance.
- Diplomatic fallback: diplomatic becomes `primary_layer=diplomatic`; no alignment is invented.
- Empty source record: one blank technical anchor; translation remains a separate textual layer.
- Translation `persName`: an `entity(kind=person)` over translation sign slots.
- Bibliography/facsimile: native metadata nodes and edges, no image bytes.

## Compatibility and consequences

Shared DSS/BHSA semantics intentionally reuse `sign`, `word`, `line`, `lang`, `glyph`, `after`,
standard sections, normal TF search/API, and a standard TF app. IIP-TF does not fabricate
lexemes, phrases, clauses, or morphology absent from IIP.

New source constructs, duplicate canonical/file-scoped identities, unresolved segmentation conflicts, or
non-deterministic projection fail explicitly rather than being hidden in a sidecar.

This ADR freezes the 0.1 semantic contract. Semantic changes require a new ADR and schema
version.

## Metadata cardinality rule

Repeatable source structures are never compressed into one scalar feature. If new full-corpus evidence shows a source child can repeat where schema 0.1 models it as scalar, conversion must stop with a schema diagnostic until the mapping is revised; it must not keep the last value.


## Audited EpiDoc coverage

The machine schema contains `source_element_mapping` and `source_attribute_mapping` for every
element and attribute name observed by the pinned corpus audit in transcription, diplomatic,
translation, commentary, explicit textparts, and segmented transcription.

Structural elements map to edition/textpart/paragraph/word nodes; inline editorial elements map
to markup; names/dates map to entity nodes; `figDesc` maps to figure description. Attribute
mappings point to explicit typed/raw features and resolved edges where appropriate.

CI compares these mapping keys directly against `docs/research/iip-inventory.json`. A future
source revision that introduces a new textual element or attribute therefore fails the mapping
gate instead of being silently ignored.
