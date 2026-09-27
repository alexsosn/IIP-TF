# IIP-TF design

**Status: frozen 0.1 semantic architecture. The normative contract is `schema/iip-tf-0.1.json` and ADR-0001.**

## System boundary

```text
Brown IIP EpiDoc source
        |
        v
source inventory / validation
        |
        v
typed canonical IR
        |
        v
native Text-Fabric writer
        |
        +----> TF corpus data
        +----> standard TF app config
        +----> build/validation report
```

The corpus graph is self-sufficient for research semantics. Build reports may use machine-readable diagnostic files, but TF consumers must not need raw XML, JSON blobs, or semantic sidecars to understand the converted corpus.

## Warp and textual hierarchy

Frozen direction:

- slot type: `sign`
- `word`: IIP token/word unit when source evidence exists
- `line`: line structure from EpiDoc
- `paragraph`: source `p`/textual `ab` block preserving block attributes and multiplicity
- `textpart`: explicit source textpart, plus a documented implicit default only where needed for a stable hierarchy
- `inscription`: one authoritative IIP record/file

A `word` can span one or more sign slots. `num` and `orig` source tokens remain distinguishable through token-kind features rather than being silently coerced to lexical words.

## Empty and zero-width source positions

Text-Fabric requires non-slot nodes to occupy slots. The release ADR must distinguish:

1. **semantic/source positions** such as explicit gaps or independently positioned empty textual material: represent with synthetic sign slots carrying no fabricated glyph;
2. **metadata-only inscriptions or repeated metadata nodes** that otherwise have no textual extent: use the smallest documented technical anchoring rule, normally reusing an inscription anchor rather than multiplying fake slots;
3. **ancestor structure**: reuse descendant anchors.

Synthetic slots never receive invented lexical or visible source text.

## Editorial markup

The graph should make common philological questions queryable without reparsing TEI.

Expected feature families include, subject to #3:

- visible/source glyph;
- language;
- source XML id;
- token kind;
- uncertainty;
- supplied/lost state and reason;
- gap reason/unit/quantity;
- expansion/abbreviation relation;
- alternative/choice identity and ordering;
- surplus/deletion-like editorial status;
- glyph reference;
- numeral value;
- hand shift/hand identity;
- source-vs-derived segmentation provenance.

Where markup spans several signs, use nodes/edges when a scalar slot feature would lose grouping or alternatives.

## Metadata model

Scalar inscription-level properties belong on `inscription` where that preserves cardinality and meaning.

Repeatable/structured records use dedicated native nodes where flattening would lose cardinality or hierarchy. Frozen 0.1 types include `bibl`, `bibl_scope`, `hand`, `dimension`, `decoration`, `facsimile_surface`, `image`, `revision`, and textual `entity`. Raw source scalars remain string-valued TF features; numeric conveniences are separate lossless derived int features.

## Translation and commentary

Translation and commentary are independent native textual layers in the same `sign` warp, each with their own edition/textpart/line nodes. They are never tokenized into or aligned with source transcription unless IIP explicitly supplies such a relation.

## Sections and navigation

The frozen browser hierarchy is:

`inscription → textpart → line`

This should be encoded through normal `otext.tf` section types/features so the standard TF browser can navigate IIP identifiers and lines.

## Compatibility policy

Compatibility with BHSA/DSS/ETCBC means:

- ordinary TF warp semantics;
- conventional structural node names where meanings match;
- familiar language/text-format behavior;
- standard app/browser loading;
- provenance in TF metadata;
- common feature names only where definitions match.

IIP-TF must not imitate BHSA morphology, lexeme, clause, phrase, or verse features that do not exist in IIP source data.

## Provenance and identity

Every release records:

- Brown source repository and exact commit;
- converter version/commit;
- unique file-stem `inscription_id` plus raw IIP/XML identifiers (which are not globally unique);
- whether token/structure information is source-provided or converter-derived;
- source licence/attribution metadata required for redistribution.

Builds from identical source + converter + supported environment should be deterministic.

## Failure policy

- unsupported source semantics are diagnostics, not silent drops;
- parse failures are explicit and source-file-accounted;
- duplicate canonical record keys or duplicate element ids within one source file fail the build; cross-file raw IIP/XML-id collisions are preserved and reported;
- unresolvable structural inconsistencies fail or are explicitly quarantined by a researched rule;
- release validation reports converted, excluded, and failed source records separately.
