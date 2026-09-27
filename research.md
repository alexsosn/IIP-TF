# Research baseline

This document records durable evidence checked before implementation. The corpus-wide measurements from issue #2 are committed in `docs/research/iip-inventory.json` and the generated `docs/research/iip-corpus-audit.md`; licensing analysis is in `docs/research/iip-licence-audit.md`.

## Upstream source

Primary source repository:

- Brown University Library, `Brown-University-Library/iip-texts`
- current observed upstream head during bootstrap: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`
- commit date: 2024-07-17
- repository README describes `epidoc-files` as the current IIP inscriptions encoded in EpiDoc XML.

The pinned issue-#2 audit accounts for **5,536 XML files** under `epidoc-files/`: 5,529 parse successfully, seven are malformed, and one parsed file is a test/non-inscription fixture. The release converter must make the seven malformed sources and the test-file exclusion explicit rather than silently reducing the corpus.

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

The full inventory confirms these common constructs and also exposes rare cases that must receive explicit #3 mapping decisions, including `app/lem/rdg`, `handShift`, `subst`, `cb`, `milestone`, `figure/figDesc`, and low-count `add/reg` usage.

## Text-Fabric precedents

BHSA uses `word` slots. ETCBC/DSS uses **`sign` slots** with higher `word`, `line`, `fragment`, and `scroll` nodes. The DSS model demonstrates that sign slots remain within the ETCBC/Text-Fabric family while supporting philological detail below the word.

For IIP, sign slots are the current design direction because:

- editorial uncertainty and supplied/lost characters can be represented at their natural extent;
- explicit gaps can occupy a source position without fabricated visible characters;
- word nodes can follow IIP segmentation when available;
- unsegmented or irregular inscriptions do not require invented word analysis;
- line/textpart/inscription nodes remain conventional TF structures.

The full audit also finds 193 records with a source transcription but no segmented transcription, at least one segmented-only case, 212 empty source transcriptions, and 47 records with explicit `textpart`. Issue #3 must therefore freeze separate policies for base-text selection, segmentation provenance, empty textual positions, and textpart navigation.

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

The authoritative IIP copyright/citation page publishes the project work under **CC BY-NC 4.0** and gives DOI `10.26300/pz1d-st89` for project citation. It also preserves contributor rights in scholarly contributions, describes inscription readings as attributed republications of source editions, and says IIP generally does not own image copyrights.

The pinned XML snapshot embeds a complete licence/DOI block in only a small subset of records, so converter licensing must follow the authoritative project-level terms rather than infer different rights from missing inline XML. Generated TF data will carry IIP attribution, DOI, exact source revision, and CC BY-NC 4.0 project terms; source-edition bibliography remains queryable, and image binaries are excluded unless separately cleared. See `docs/research/iip-licence-audit.md`.

Software authored in IIP-TF remains MIT licensed independently from source/generated corpus data.
