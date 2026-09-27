# Research baseline

This document records evidence already checked before implementation. It is intentionally incomplete; issue #2 must replace sample-based assumptions with corpus-wide measurements.

## Upstream source

Primary source repository:

- Brown University Library, `Brown-University-Library/iip-texts`
- current observed upstream head during bootstrap: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`
- commit date: 2024-07-17
- repository README describes `epidoc-files` as the current IIP inscriptions encoded in EpiDoc XML.

A bootstrap tree inventory found roughly 5.5k XML files under `epidoc-files/`; issue #2 must produce the authoritative release count and exclude test/non-inscription files explicitly.

## Word segmentation evidence

`word-segmentation/README.md` documents IIP's segmentation workflow:

- it copies `div type="edition" subtype="transcription"` to `transcription_segmented`;
- tokens are wrapped as `w`, `num`, or `orig`;
- token elements receive language and sequence-bearing XML identifiers;
- word lists are produced by language for later linguistic analysis;
- the workflow explicitly says it does not yet handle `@textpart` divs;
- failed/unsegmented files can remain outside the successful output.

Consequences for IIP-TF:

1. `transcription_segmented` is valuable authoritative token evidence when present.
2. Its absence cannot be treated automatically as evidence that there is no text.
3. The converter must not silently pretend that all inscriptions have homogeneous word segmentation.
4. A sign-slot warp can preserve textual order and editorial detail without forcing guessed word boundaries.

## Sampled EpiDoc constructs

Representative inspected files include `arad0001.xml`, `lach0001.xml`, `idum0001.xml`, `caes0001.xml`, and `jeru0001.xml`.

Observed textual constructs include:

- `w`, `num`, `orig`;
- `lb`;
- `unclear`;
- `supplied reason="lost"`;
- `gap` with reason/unit/quantity;
- `expan`, `abbr`, `ex`;
- `choice`;
- `surplus`;
- `g ref=...`;
- `handShift`;
- language annotations at multiple levels.

Observed non-textual research metadata include:

- IIP/XML identifiers;
- language declarations;
- inscription type and religious/cultural classification;
- object/support/material/condition;
- dimensions and layout;
- hands/writing technique;
- decoration and locus;
- date ranges and PeriodO references;
- region, settlement, site/locus and Pleiades references;
- provenance/current location;
- facsimile graphics/descriptions/notes;
- bibliography pointers and scoped references;
- revision history and contributor information.

These examples justify a native graph model, but they do not prove complete corpus coverage. Issue #2 must inventory all element/attribute patterns.

## Text-Fabric precedents

BHSA uses `word` slots. ETCBC/DSS uses **`sign` slots** with higher `word`, `line`, `fragment`, and `scroll` nodes. The DSS model demonstrates that sign slots remain within the ETCBC/Text-Fabric family while supporting philological detail below the word.

For IIP, sign slots are the current design direction because:

- editorial uncertainty and supplied/lost characters can be represented at their natural extent;
- explicit gaps can occupy a source position without fabricated visible characters;
- word nodes can follow IIP segmentation when available;
- unsegmented or irregular inscriptions do not require invented word analysis;
- line/textpart/inscription nodes remain conventional TF structures.

Issue #3 must freeze the precise schema after #2 measures the full source.

## Standard web interface

The intended web interface is the standard Text-Fabric app/browser, using `app/config.yaml`, text formats, type displays, provenance configuration, and normal `tf.app.use()` / browser launch paths. No custom web application is planned for 0.1.

## Agora materializer contract

Agora's current materializer contract v1:

- runs a declared Python module;
- permits only `{source}`, `{output}`, and `{source_revision}` placeholders;
- denies network during execution;
- supports public pinned Git acquisition and user-local directories;
- validates declared required output paths;
- treats Python installation/execution as explicit third-party code trust.

IIP-TF should eventually publish `agora.materializer.json` from this repository. Agora should pin an immutable IIP-TF release/ref and must not reimplement EpiDoc conversion semantics. Upstream implementation is issue #11; downstream registration is Agora issue #187.

## Licence evidence

Many current IIP XML records explicitly state Creative Commons Attribution-NonCommercial 4.0 International and require reuse/distribution to include a link to the IIP DOI `10.26300/pz1d-st89`.

Some older/current files use XInclude or differ structurally, so the bootstrap does **not** claim that every source component has already been audited under one uniform licence statement. Issue #2 must establish the defensible corpus-wide licence/redistribution conclusion before generated data are published.

Software authored in IIP-TF is intended to be MIT licensed independently from source/generated corpus data.
