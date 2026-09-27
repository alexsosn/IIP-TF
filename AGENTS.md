# IIP-TF agent instructions

IIP-TF is designed for autonomous, issue-driven development. Coding agents must treat this file as the mandatory entry point.

## Read first

Before changing code or corpus semantics, read in order:

1. `README.md`
2. `research.md`
3. `design.md`
4. `plan.md`
5. `LICENSE_SCOPE.md`
6. `docs/agentic-dev-loop.md`
7. the active GitHub issue and all linked PR/review discussion

When work depends on Brown IIP/EpiDoc, Text-Fabric, ETCBC/BHSA/DSS, or Agora behavior, verify the current upstream contract rather than relying on memory.

## Development gates

Every behavior change follows:

**research → plan/design → RED-first TDD → implementation → exact-head tests → logically independent adversarial review**

- Work from a GitHub issue with explicit acceptance criteria.
- Check for overlapping open issues and PRs before starting.
- Preserve a deterministic failing test before a production behavior fix.
- Keep research/design evidence proportional to risk, but do not skip it for semantic mapping changes.
- A review is valid only for the exact final head. Production changes after review invalidate approval.
- Review fixes that change behavior repeat RED → fix → GREEN → re-review.
- Do not merge a release-critical change with unexplained corpus failures or silent partial success.

Research may create focused new issues when actual source evidence reveals missing work. Do not manufacture speculative architecture or expand release scope without evidence.

## Corpus semantics

The source of truth is Brown University Library's IIP EpiDoc corpus.

Non-negotiable rules:

- Do not store source semantics as raw XML/JSON blobs merely to avoid modelling them.
- Do not require semantic sidecars when the information can be represented as TF nodes, edges, or features.
- Preserve upstream readings, uncertainty, identifiers, dates, references, and editorial judgments; do not silently improve or normalize them.
- Do not invent morphology, lexemes, translations, segmentation, or reconstructed text.
- Distinguish source data from converter-derived structure with explicit provenance features.
- Source-critical zero-width/empty textual positions stay in TF through explicit synthetic slots when required by the frozen ADR.
- Metadata-only technical anchoring must be bounded, documented, and must never fabricate visible text.
- Unknown/unsupported EpiDoc constructs must be measured and reported. Silent dropping is a bug unless the frozen schema explicitly classifies them as non-semantic and ignorable.

## Text-Fabric compatibility

The initial architecture uses `sign` slots and ordinary `word`, `line`, `textpart`, and `inscription` nodes, following the ETCBC/DSS precedent where it matches IIP.

Compatibility means shared semantics, not cosmetic aliases:

- reuse established TF/ETCBC names when they mean the same thing;
- document deliberate differences;
- never create BHSA-style morphology features when IIP does not supply that analysis;
- validate output by loading it with the supported Text-Fabric release.

## Agora boundary

IIP-TF owns parsing, normalization, scholarly semantics, TF construction, validation, app configuration, and source-specific documentation.

Agora owns acquisition/execution integration, sandbox/trust UX, registry metadata, artifact publication/provenance, and marketplace consumption.

If the same semantic bug exists when IIP-TF runs directly, fix it here rather than in Agora.

## Release mode

Issue #12 is the 0.1.0 release gate. Prefer work that closes an explicit dependency of that gate. A prototype is not a release merely because it converts a sample.
