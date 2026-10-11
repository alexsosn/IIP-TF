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
| `text-orig-refs-full` | Explicit primary reading with source-empty glyph identifiers in IIP `((ref))` notation; these tokens are **not attested source letters**, nor Unicode substitutions |
| `text-section-normalized-full` | Normalized signs in **each selected textpart/line**, including secondary diplomatic, translation and commentary; browser default only; inscription-level aggregation concatenates distinct layers and is **not a unified primary reading** |
| `text-source-full` | Source-oriented primary reading |
| `text-layer-full` | Literal stored-slot view of one edition/textpart/line; may expose both editorial branches |
| `text-transcription-full` | Normalized transcription layer |
| `text-diplomatic-full` | Diplomatic layer |
| `text-translation-full` | Translation layer |
| `text-commentary-full` | Commentary layer |
| `word-default` | Word-node display |

The **core corpus default** remains `text-orig-full` and uses
`primary_glyph` / `primary_after`, undefined on non-primary slots.
The **standard TF browser** chooses the additive
`text-section-normalized-full` view for the selected textpart/line.
It concatenates the four existing, mutually layer-exclusive,
**normalized-only** per-layer glyph/after pairs. This reveals the
non-primary diplomatic text of `haif0003` and translation of
`bloy0002` without duplicating `orig/reg` alternatives. It adds no
source glyph data and does not modify `api.T.defaultFormat` or existing
Text-Fabric MCP/API results. Query an entire inscription with this
format only if you intentionally want *all* its textual layers
concatenated, not one inscription reading.

The **opt-in** `text-orig-refs-full` uses
`{primary_glyph}{primary_ref_token}{primary_after}` and retains primary
normalized selection, including diplomatic fallback. The `primary_ref_token`
feature is *sparse*: it appears only on selected primary zero-width
`synthetic_kind=glyph_ref` slots with a nonempty source `markup ref`.
The derived label `((ref))` follows the earlier IIP published display
convention. It is **not attested source text** or a Unicode transliteration,
and it never changes `glyph`, `primary_glyph`, `text-orig-full`, source
`ref`, or the `T.text` default. HTML-sensitive source ref characters
are entity-escaped in these visible tokens only, leaving the native
`markup` `ref` verbatim. For text-level discovery of those tokens choose
the explicit format, and use `markup kind=glyph ref=...` to query the
source annotation. Glyphs missing a source `ref` are not fabricated;
nonprimary textparts still need an explicit layer format (#51).

## Text language provenance (issue #53)

The `lang` feature on a sign denotes its textual language, not
necessarily the language of the inscription's `textLang/@mainLang`.
Inscription-level `main_lang` remains source-valued and applies by
default only to source `transcription` / `diplomatic` editions.

For `translation` and `commentary`, which in this pinned IIP corpus
are English prose unless explicitly marked otherwise, the converter assigns
`lang=eng` and **`lang_source=layer:translation`** or
**`layer:commentary`**. This is a *converter inference*, not a
source-declared ISO language. An explicit `xml:lang` on a division,
paragraph, or inline foreign-language span takes precedence and has
`lang_source=xml:lang` or `inherited` at the sign, as applicable.
The edition/paragraph markup retains its native source language annotation.

This bounded correction does **not** yet reinterpret the origin of names
marked with `persName@xml:lang` (#55), distinguish container script
from spoken language (#54), or normalize codes (#52/#57). The additive
#54 provenance slice described below retains parser-visible raw attributes,
but source `lang` values are still not ISO-normalized or corrected.

## Amendment #54-B — explicit XML language-source provenance

`lang_original` is the **literal source `xml:lang` attribute value exposed by the
XML parser**, including leading/trailing spaces, where there was an explicit
source language declaration. It is propagated to descendants of that element,
but is **absent** when `lang` was inherited only from record `textLang/@mainLang`
or inferred as English from a translation/commentary layer. XML normalization
(such as entity expansion) means this is not a reconstruction of raw XML bytes.

`lang_origin` records the local TEI name of the nearest declaring element,
for example `p`, `foreign`, `div`, `w` or `num`. It survives descendant
`lang_source=inherited`, so a later safe #54 correction can distinguish
paragraph script-like declarations from explicit foreign-language content.
For aligned segmented `word` nodes and projected segmented markup, the two
features preserve the source token/inline attribute independently of the
sign it annotates. Existing `lang`, `lang_source`, `script`, TF text and source
glyph/slot identity are unchanged; #54 and #57 remain open.

## Amendment #54-C — selected source-word language precedence

For an Aramaic inscription with a transcription paragraph declaring
`xml:lang=heb` as a script-like label, a **drift-free, source-backed,
selected segmented** `word` with `lang=arc` can relabel its aligned
Hebrew-encoded letter signs to `lang=arc` and
`lang_source=transcription_segmented`. `lang_original=heb` and
`lang_origin=p` still preserve the source paragraph declaration,
and the independent `script=Hebr` remains the encoded alphabet.
A conflicting overlapping projected word language fails the build.

An explicit `foreign` annotation, `p` with no projected token,
a source-drift token, punctuation, a technical glyph/gap, any other
text layer and non-Aramaic record remain unchanged. This limited
rule does **not** promise ISO 639-3 normalization or complete Aramaic
coverage; #54, #52 and #57 remain open.

## Amendment #90 — division-origin Aramaic source precedence

For `main_lang=arc` *transcription* Hebrew-encoded letters with original
source `xml:lang=heb` declared by a `p` or edition `div`, an
explicit, selected drift-free aligned `w@xml:lang=arc` outranks
script-like container `heb` in the effective sign `lang` only.
The literal `lang_original`, declaring `lang_origin`, encoding-derived
`script`, and original glyph remain independently queryable. No inference
for unaligned signs or questionable/contradictory segmented evidence.
See #54, #90, ADR-0001.

## Slot features

Core features include `glyph`, `after`, `layer`, `lang`, `lang_source`, `script`,
`script_source`, `reading_role`,
`synthetic_kind`, primary/source display pairs, the sparse derived
`primary_ref_token` used by the opt-in source-reference view, and layer-specific
glyph/after pairs.

The additive native `script` on signs and single-script projected words is an
**ISO 15924 classification of encoded Unicode letters**, not a claim about
the ancient inscription's original script. Its separate
`script_source=encoded_unicode` records this derivation. Unsupported
letters, punctuation, combining marks, numbers, mixed-script words and
technical gap/glyph-reference positions remain unclassified.
For example: `chor0001` has encoded `Hebr` characters in Aramaic
inscriptions, `beth0023` has Greek-script `arc-Grek` text, and
`sina0114`'s Latin transliteration is `Latn` *as stored text*.
The original `lang` values remain unchanged in this first #54 slice;
they must not be interpreted as normalized language identity until the
separate source-backed #54/#57 correction is completed.

`synthetic_kind` covers anchor, line/column break, gap, space, hand shift, milestone,
glyph reference, figure, and other audited point events.

## Common node features

All source nodes use `source_id` when `xml:id` exists, otherwise deterministic `source_key`.
Editorial fields include kind/layer/language, reason, certainty, unit, quantity, extent,
bounds, precision, ref, value, rend, type, place, evidence, break, and hand reference.

Raw source values remain available when a typed/derived value is also supplied.

**Inline whitespace ownership.** A sparse native `markup` feature
`source_trailing_space_inside=yes` distinguishes
`<supplied>BC </supplied>D` from `<supplied>BC</supplied> D` when
both normalize to the same source reading `BC D` and the same
`C.after=" "`. It records that the **normalized trailing space was
already present when that source element closed**, before its
surrounding `tail` was consumed. Query the markup node's feature
directly; the standard TF browser places closing labels after an
inside-owned space and before an outside-owned space, with nested
inner-before-outer order preserved.

This is **not** a character-for-character copy of the original XML
whitespace: tabs, multiple spaces and newlines are governed by the
existing source-space normalization, and no whitespace slots or new
raw-text sidecars are introduced. The original `glyph`, `after`
and all Text-Fabric `fmt` outputs remain unchanged. The feature is
absent on markup where no such normalized inside space exists.

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
