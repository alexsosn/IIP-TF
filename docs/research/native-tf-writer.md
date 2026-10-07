# Research — native Text-Fabric writer

Issue: #5.

Research date: 2026-10-08.

## Scope

Serialize the already-final canonical `InscriptionIR` graph as a standard,
self-contained Text-Fabric 13.1.x dataset without reinterpreting EpiDoc.

This research follows ADR-0001, ADR-0002 and the #43 zero-span point model.

## Pinned canonical-IR writer audit

A reproducible audit is retained in
`scripts/research_issue5_writer_contract.py`. Against the pinned Brown
revision it reports:

- 5,535 parsed records;
- 1,466,387 sign slots;
- 308,290 non-slot IR nodes;
- 380,645 semantic edges;
- 49 zero-width point nodes;
- 11,427 empty structural edition/paragraph nodes;
- 0 duplicate global canonical keys.

Semantic edge counts are:

| edge | count |
| --- | ---: |
| `parent` | 238,889 |
| `in_inscription` | 75,161 |
| `token_from` | 39,463 |
| `cites` | 18,011 |
| `segmentation_of` | 5,167 |
| `corresponds_to` | 3,954 |

The audit also confirms that every retained `after` separator in the pinned IR
is a single space (267,141 occurrences). When editorial branches are suppressed,
separator transfer is required in real data: 351 normalized and 2,599
source-oriented transcription intervals, plus 14/21 diplomatic intervals.
This makes separator transfer a source-grounded writer requirement rather than
a synthetic fixture concern.

All existing node features are single-typed in the pinned IR. In addition to
the originally documented numeric derivatives, `candidate_index`, `selected`,
and `token_count` are integer-valued. Schema 0.1 and the writer declare those
as int features, together with serializer-derived `point_index`.

## Text-Fabric API choice

Text-Fabric 13.1.0 exposes two relevant paths:

1. `tf.convert.walker.CV`, which builds graph semantics while source material is
   being walked and checks active section nesting while slots are emitted;
2. `tf.fabric.Fabric.save()`, which writes already-materialized node/edge
   dictionaries and validates `otype`/`oslots`.

IIP-TF already has the full semantic graph before serialization. Re-entering it
through `CV` would add an unnecessary lifecycle: section nodes would have to be
opened while slots are recreated even though canonical IR already contains the
final spans. Direct `Fabric.save()` maps the IR boundary more faithfully and
still uses Text-Fabric's own writer and warp validation.

Decision: **use `Fabric.save()` directly**.

## Global node/slot numbering

The generated TF graph uses normal integer TF node ids.

- records are sorted by canonical `inscription_id`;
- all signs are emitted first, record by record and in canonical IR sign order;
- slots are therefore exactly `1..maxSlot`;
- non-slot nodes follow;
- non-slot types are grouped by schema 0.1 node-type order, then record id, then
  canonical node key.

Grouping non-slots by type keeps `otype.tf` compact while preserving fully
deterministic numbering. Canonical source identities remain features/keys; TF
node integers are serialization ids only.

The writer must reject duplicate canonical sign/node keys across records rather
than allowing later dictionary entries to overwrite earlier ones.

## `oslots` policy

### Non-empty semantic nodes

Map exactly to their canonical `sign_keys`.

### Empty structural nodes

Pinned-corpus research for #43 found empty semantic spans only on `edition`,
`paragraph`, and `markup`.

Empty `edition`/`paragraph` nodes have no point semantics. Text-Fabric still
requires every non-slot node to have a non-empty `oslots` set, so they receive
the record's **technical primary anchor**:

- first slot in `primary_layer` when primary is transcription/diplomatic;
- the existing synthetic `anchor` slot for records with no primary source text.

They expose `empty=1`, making the technical `oslots` anchor explicitly
non-semantic.

Unexpected empty node types without `point_index` fail closed.

### Zero-width semantic point nodes

`IRNode.point_index` is a record-local boundary offset.

Encoding:

- if `point_index < len(signs)`, anchor technically to
  `signs[point_index]` and write `point_relation=before`;
- if `point_index == len(signs)`, anchor to the final sign and write
  `point_relation=after`;
- write the original integer `point_index` as an int feature as an explicit
  audit/round-trip value.

The adjacent anchor plus relation reconstructs the point even without trusting
the copied integer. The writer verifies this reconstruction before save.

Because every parsed record has at least one sign (real primary text or the
single schema-defined empty-record anchor), an adjacent technical anchor always
exists.

## Semantic edge features

Every canonical `IREdge.edge_type` becomes a normal unvalued TF edge feature.

The writer resolves endpoints through the same global key->TF-node map used for
node features and fails on an unknown endpoint.

No source relation is encoded as opaque JSON/XML.

## Slot features and display views

Raw slot features come directly from `IRSign`:

- `glyph`
- `after`
- `layer`
- `lang`
- `lang_source`
- `reading_role`
- `synthetic_kind`

Derived display features implement schema 0.1 without reparsing TEI.

Normalized selection accepts reading roles `both` and `normalized`; source
selection accepts `both` and `source`.

Derived views:

- `primary_glyph/primary_after`: normalized selected reading of the record's
  primary layer;
- `source_glyph/source_after`: source selected reading of the primary layer;
- `transcription_*`, `diplomatic_*`, `translation_*`,
  `commentary_*`: normalized selected reading for that layer.

Separators attached to a suppressed alternative cannot simply disappear. When a
suppressed sign carries `after`, the writer transfers that separator to the
nearest preceding selected sign in the same layer. This covers shapes such as an
expansion whose trailing whitespace is attached to an `ex` sign that is
suppressed in source-oriented display.

The existing `text-layer-full={glyph}{after}` is retained as a literal stored
slot view; it can expose both editorial branches. Schema/reference prose should
say so explicitly. Selected display uses the primary/source/layer-specific
derived formats.

## Text configuration

`otext.tf` declares:

- `sectionTypes=inscription,textpart,line`;
- `sectionFeatures=inscription_id,section_part,line_n`;
- the schema 0.1 text formats.

Text-Fabric's section preparation indexes the section nodes that exist. It does
not require creation of a fake textpart/line for the technical anchor of the 18
records with no source text. The writer must load a fixture with such an anchor
through Text-Fabric to prove this.

## Feature typing

Text-Fabric requires one `valueType` per feature.

Schema 0.1 integer node features remain int:

- `line_n`
- `quantity_int`
- `date_not_before_int`
- `date_not_after_int`

Writer-derived `point_index` is also int. Point serialization is permitted on\ninline semantic `markup` and `entity` nodes, matching the canonical #43 IR contract.

All remaining slot/node features are strings. All canonical edge features are
unvalued edges.

The writer fails closed if one TF feature receives mixed Python value types.

## Provenance metadata

Generic metadata written into every TF feature:

- `source=Inscriptions of Israel/Palestine, Brown University`
- `sourceUrl=https://github.com/Brown-University-Library/iip-texts`
- `sourceCommit=<pinned/requested source revision>`
- `sourceDOI=10.26300/pz1d-st89`
- `license=CC BY-NC 4.0`
- `licenseUrl=https://creativecommons.org/licenses/by-nc/4.0/`
- `converterVersion=<iip-tf package version>`
- `converterCommit=<explicit converter commit>`
- `schemaVersion=0.1`

All IRs in one output must have the same source revision.

## Deterministic output

Text-Fabric 13.1.0 sorts feature names and node/edge dictionaries during write,
but every `.tf` file receives a current `@dateWritten` header.

For byte-stable generated feature files:

1. write through `Fabric.save()`;
2. remove only the `@dateWritten=...` line from every top-level `*.tf` file;
3. load the normalized result with Text-Fabric itself;
4. remove Text-Fabric's optional binary cache directory from the artifact.

The writer never rewrites data lines itself.

## Validation gates

Unit/fixture gates:

- standard warp/config files are written and loadable;
- deterministic rebuilds are byte-identical;
- semantic edges round-trip;
- zero-width point position reconstructs from technical anchor + relation;
- empty structural nodes remain explicitly empty despite technical `oslots`;
- normalized/source display alternatives differ correctly;
- a no-source-text record loads without invented line/textpart nodes.

Pinned-source gate:

- parse all 5,535 non-test records at the pinned Brown revision;
- serialize one complete TF dataset;
- Text-Fabric loads it successfully;
- all non-slot nodes have valid `oslots`;
- canonical node/edge counts are preserved;
- all 49 semantic zero-width markup points remain reconstructable.

#7 remains responsible for the final release conversion report and whole-build
reproducibility acceptance, but #5 must already prove the writer itself on the
complete pinned corpus.
