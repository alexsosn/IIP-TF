# Issue #3 plan — freeze native Text-Fabric schema

## Goal

Freeze the first-release IIP-TF graph contract before parser/writer implementation.

The schema must preserve all research-relevant IIP semantics natively in Text-Fabric while remaining comfortable for users of BHSA/DSS-style corpora.

## Research inputs

This design consumes the merged evidence from #2, #16, #18, #20, current Text-Fabric text/section/format semantics, and ETCBC/BHSA/DSS naming conventions where meanings genuinely match.

## Architectural decisions to freeze

1. **Warp** — one `sign` slot type; all genuine textual layers live in the same warp; `transcription_segmented` is annotation/provenance, not a duplicated text layer.
2. **Textual layers** — native sign slots for normalized transcription, diplomatic, translation, commentary; explicit `edition`, `textpart`, and `line` nodes; `inscription` spans all textual slots; default text format renders only the selected primary source-text layer.
3. **Primary source text** — non-empty normalized transcription first; otherwise non-empty diplomatic text; otherwise one synthetic technical anchor and empty primary text; segmented transcription never becomes a competing primary edition by itself.
4. **Words** — `word` nodes come only from validated IIP `transcription_segmented` boundaries; boundaries are projected onto primary source-text slots only when deterministic; no whitespace-tokenization fallback and no invented morphology; duplicate segmented editions use the #20 resolver and fail closed on unknown conflicts.
5. **Editorial semantics** — source-critical zero-width positions receive explicit synthetic sign slots in source order; inline editorial constructs become structured `markup` nodes with enumerated `kind` plus typed scalar features and direct-parent edges; no raw XML, JSON attribute blobs, or opaque TEI fragments.
6. **Sections and web usability** — `sectionTypes=inscription,textpart,line`; section headings are stable and layer-aware; standard TF formats include primary, generic-layer, transcription, diplomatic, translation, and commentary views; a normal Text-Fabric app may style these, but no separate web application is required.
7. **Metadata** — one-to-one scalar physical/origin/provenance fields live on `inscription`; repeatable/structured bibliography, hands, decorations, facsimile references, and revision history become native TF nodes; image binaries are not copied; URLs/credits remain metadata.
8. **Provenance and identity** — exact Brown source revision, DOI, project licence, converter and schema version; source XML ids retained when present; deterministic derived `source_key` for elements without ids; raw source values retained when derived/canonical values are additionally exposed.

## Deliverables

- `schema/iip-tf-0.1.json`: machine-readable graph contract;
- `docs/architecture/ADR-0001-native-tf-schema.md`: rationale, mapping and examples;
- `docs/reference/schema-0.1.md`: researcher-facing node/feature reference;
- tests that fail before the contract exists and enforce the non-negotiable decisions.

## TDD gate

RED tests are committed before the schema files. They assert the single sign warp, four native textual layers, primary fallback order, annotation-only segmentation, section hierarchy, required structural/metadata node types and features, no-blob/no-sidecar policy, synthetic anchor rules, and source-rights provenance.

## Done

#3 is complete only after the machine-readable schema, ADR and researcher reference agree, tests are green, and an exact-head logically independent adversarial review finds no semantic-loss or ergonomics blocker.
