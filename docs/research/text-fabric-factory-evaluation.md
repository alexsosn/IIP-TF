# Research — text-fabric-factory for IIP-TF

Issue: #41.

Research date: 2026-10-03.

## Scope

This evaluates whether `annotation/text-fabric-factory` (TFF), especially
`tff.convert.tei`, should replace or sit inside IIP-TF's pinned-source
EpiDoc -> canonical IR -> native Text-Fabric pipeline.

The decision is constrained by ADR-0001/schema 0.1. IIP-TF must keep a
`sign` warp, semantic node types, source-critical zero-width positions,
selected segmented-word provenance/projection, explicit metadata cardinality,
file-scoped identity, and fail-closed source handling. A generic
TEI-element-to-TF transcription is not schema-compatible merely because it
produces loadable TF.

## Upstream package inspected

Pinned TFF source for this evaluation:

- repository: https://github.com/annotation/text-fabric-factory
- commit: `bae4a39d298ab6a44668b37e565d799d11f9a244` (2025-12-04)
- package: `text-fabric-factory 1.0.8` (PyPI, 2025-12-04)
- licence: MIT
- Python: >= 3.9
- package status: Beta
- direct dependency: `text-fabric` without an upper bound in TFF 1.0.8
- GitHub Releases: none; PyPI exposes 1.0.0 and 1.0.8

The package is installable alongside IIP-TF's Python floor. The dependency
surface is nevertheless wider than IIP-TF's current direct use of
`text-fabric>=13.1,<14`: TFF adds a second release/pinning boundary and its
setup metadata does not constrain the Text-Fabric major version.

TFF bundles generic TEI XSD/RNG material and has JING/TRANG-based schema
tooling. For custom Relax NG models, its documentation says it uses JING for
validation and TRANG to derive XSD for element analysis; that path introduces
Java/tooling concerns beyond IIP-TF's current Python-only conversion path.

## Architectural comparison

### IIP-TF's frozen boundary

IIP-TF's parser emits a TF-independent canonical IR. Text parsing, metadata
parsing, source repair, duplicate segmented-edition resolution, and segmented
annotation projection all finish before TF serialization.

That boundary is already doing corpus-specific semantic work which cannot be
delegated to a generic TEI walker:

- one visible `sign` is one Unicode code point;
- ordinary XML whitespace is not a slot;
- source-critical point events such as `lb`, `gap`, `space`,
  `handShift`, `milestone`, empty glyph refs and figures get one typed
  synthetic position;
- `word` nodes come only from selected IIP segmentation projected
  deterministically onto primary source slots;
- normalized/source reading alternatives remain separate queryable markup;
- TEI header/facsimile/bibliography structures map to the frozen semantic
  metadata node vocabulary rather than becoming generic TEI nodes;
- seven malformed pinned source files receive revision-scoped researched
  repairs; unknown corruption fails closed;
- the pinned full-source gate currently accounts for all 5,536 XML files,
  parses all 5,535 non-test records, applies exactly seven researched repairs,
  and projects 39,472 selected segmented token identities.

### TFF vanilla TEI model

The inspected TFF implementation is deliberately generic and has conventions
which conflict with that contract.

#### 1. Slot model

TFF `granularity` supports only `word`, `token`, or `char`. In char
mode, all characters are slots; in token/word modes TFF derives tokens/words
from text itself.

That is not IIP-TF's `sign` model. IIP-TF needs visible code-point slots but
moves ordinary whitespace into rendering separators and injects typed
zero-width source positions. TFF's derived word/token modes are also
semantically disallowed for IIP-TF because IIP words must come from the
audited `transcription_segmented` source and deterministic projection.

Renaming TFF's `char` slot type to `sign` would not solve this: the slot
population and the semantics of empty/point elements still differ.

#### 2. Element -> node behaviour

TFF's walker creates `cv.node(tag)` for every TEI element except its tiny
`PASS_THROUGH` set (currently only `TEI`) and special line/page boundary
cases.

This directly conflicts with schema 0.1. IIP-TF must not create node types
merely because XML elements exist. For example, `choice`, `sic`, `corr`,
`supplied`, `gap`, `g`, `figure`, `biblScope`, `surface`, etc. map
into a small semantic vocabulary (`markup`, `bibl_scope`,
`facsimile_surface`, ...).

The custom hooks run around the vanilla walk, but the default node has already
been created before `beforeChildrenCustom`. Replacing the native mapping
would therefore require fighting/deleting/reimplementing the generic walk
rather than configuring a clean semantic mapping.

#### 3. Namespace semantics

TFF converts element and attribute names with
`etree.QName(...).localname`; its hook API documents tag/attribute names as
having namespaces stripped.

IIP-TF has just hardened metadata parsing specifically so foreign or explicitly
unnamespaced elements cannot alias audited TEI names. A parser frontend that
drops namespaces before semantic validation weakens that invariant. Keeping TFF
would require validating the original LXML QNames independently before the
TFF-localname layer, eliminating much of the proposed frontend benefit.

#### 4. Header and metadata

TFF walks `teiHeader` as content and marks its generated slots/words with
`is_meta`. It also creates TEI-element nodes and copies attributes as
features.

IIP-TF intentionally does not create a parallel header text. One-to-one values
live on `inscription`; repeatable structures become the frozen metadata node
types, technically anchored to an existing primary source slot and connected
through semantic ownership. Cardinality violations fail closed.

Using TFF as the metadata frontend would therefore require reconstructing the
same path-aware metadata parser after TFF has already emitted the wrong graph.

#### 5. Source repair and failure policy

TFF's XML parser uses ordinary LXML parsing with no recovery. On parse failure,
the conversion logs that the file is skipped and continues.

That is incompatible with the IIP-TF release gate. At the pinned Brown revision,
seven files contain literal unresolved Git-conflict markers. IIP-TF applies
seven exact, revision-scoped researched repairs and requires 5,535/5,535
non-test records to parse. Silent/continued omission of those records is not an
acceptable fallback.

TFF offers a whole-file `transform(text)` hook, so the seven repairs could be
ported into a TFF customization, but that merely moves existing IIP-specific
logic and still needs the same revision/hash/provenance guards.

#### 6. IDs and relations

TFF has generic support for `xml:id` and local references from selected
elements (`ptr@target`, `ref@target`, `rs@ref`).

IIP-TF needs a stronger file-scoped identity contract because the corpus has
cross-file duplicate `xml:id` and IIP ids. It also preserves and resolves
IIP-specific `@corresp` relations and never lets derived identities overwrite
raw source values. TFF's generic relation handling is useful reference code,
but it does not replace this contract.

#### 7. Generated app/docs

TFF can generate a TF app and transcription documentation. IIP-TF does plan a
standard TF app, so this is the clearest reusable idea.

It is not a reason to adopt the TEI converter. App generation is downstream of
the semantic corpus. We can inspect/reuse the conventions later in #8 without
making TFF a conversion dependency.

## Real IIP cases

### `idum0375.xml`

The normalized transcription contains `gap`, `lb`, and a `choice` of two
`unclear` readings. The selected segmented edition contains the corpus's
audited `app/lem/rdg` case inside one `w`.

IIP-TF projects that segmented annotation onto the existing primary sign
sequence without making a fifth text. Vanilla TFF instead walks the segmented
edition as another TEI text subtree, creates element-named nodes, and derives
slots from its content. Preserving the IIP semantics therefore still requires
the existing duplicate resolver and projection algorithm outside/around TFF.

### `mgha0001.xml`

The transcription has `choice/sic/corr` and an `lb break="no"` inside a
word; the segmented edition omits that line break. The facsimile also contains
a nested `surface`.

IIP-TF's word projection deliberately spans the existing zero-width line-break
slot and its metadata parser preserves the nested surface parent relation.
Generic character walking does not supply either semantic decision.

### `masa0779.xml`

This is the audited record with segmented text but no normalized transcription;
diplomatic text is the primary source layer. IIP-TF projects segmentation onto
the selected primary layer rather than assuming normalized transcription.
That selection/projection rule is corpus-specific and outside TFF's generic
TEI conversion model.

### `caes0433.xml`

The pinned file is not well-formed because the facsimile contains unresolved
Git conflict markers. IIP-TF applies the researched union repair only for the
exact pinned revision and exact conflict block. TFF's vanilla parser would
skip the file after the parse error; a transform hook could only reimplement
the existing repair.

### `akld0007.xml`

The physical-support prose contains the single audited nested
`support/p > foreign` shape. IIP-TF permits that exact transparent child
while validating TEI namespaces and preserving the path-specific semantic
field. TFF's local-name normalization is too permissive for this boundary.

## Options

### A. TFF as primary conversion engine

Rejected. Its slot population, element-node graph, header handling, namespace
normalization, source-error policy, and segmented-text behavior all disagree
with schema 0.1. Customizing enough hooks to restore the IIP contract would
amount to a second implementation of the current parser inside TFF's stateful
walker.

### B. TFF as parsing/schema frontend, retain canonical IR

Rejected for production. TFF's useful TEI-specific analysis is coupled to its
conversion conventions and strips namespaces in the walk. We would still need
our own namespace-aware semantic traversal, source-repair gate, identity
policy, and all IIP-specific projection/cardinality validation before creating
IR. The dependency would not remove the complex code.

### C. Use lower-level `tf.convert.walker`

Keep as a candidate implementation detail for #5, not a consequence of
adopting TFF. IIP-TF already depends directly on Text-Fabric, and TFF itself
builds on `tf.convert.walker.CV`. If the writer benefits from the walker,
using it directly keeps the canonical IR boundary and avoids importing TFF's
TEI semantics.

### D. Reference/reuse selected TFF design patterns only

Accepted.

Useful material to reuse or compare against:

- `tf.convert.walker` orchestration patterns;
- feature metadata/app-generation conventions;
- XML schema inventory/validation ideas as optional development tooling;
- generic reference-resolution/reporting patterns;
- tests/ideas around line/page modelling where they fit the frozen IIP schema.

No production dependency is needed for these benefits.

## Performance decision

A whole-corpus TFF speed/memory bake-off is not decision-relevant after the
semantic compatibility gate fails. A fast conversion to the wrong graph is not
an alternative implementation of IIP-TF.

The relevant current baseline remains the exact IIP pipeline. The most expensive
known stage is segmented projection; after its bounded matching work the pinned
whole-corpus parse was roughly 61 seconds on the GitHub runner, and the current
full-source gate completes with zero projection failures.

A TFF performance spike would require first implementing enough custom hooks to
reproduce the frozen schema, source repair, segmented projection and metadata
cardinality. That implementation would be the migration itself, not a cheap
benchmark. #41 therefore deliberately stops before that sunk-cost experiment.

## Decision

**Use text-fabric-factory as implementation/reference material only; do not add
it as an IIP-TF production dependency and do not replace the canonical parser
or IR boundary with `tff.convert.tei`.**

For the native writer (#5), evaluate the already-available
`tf.convert.walker.CV` directly against the IR writer requirements. For the
standard app (#8), inspect TFF's generated-app conventions separately. Neither
follow-up requires TFF at runtime.

## Revisit conditions

Reopen this decision only if one of the following changes materially:

1. schema 0.1 is superseded by an ADR that permits element-shaped TEI TF;
2. TFF gains a first-class semantic mapping mode that can suppress/transform
   vanilla element nodes before creation, preserve namespace identities, and
   accept externally supplied slot/event identities;
3. TFF exposes a decoupled TEI analysis frontend that returns a namespace-aware
   intermediate representation without creating TF;
4. a future IIP source model becomes close enough to TFF's vanilla conventions
   that the custom semantic layer would actually shrink.
