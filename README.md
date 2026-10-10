# IIP-TF

IIP-TF converts the [Inscriptions of Israel/Palestine (IIP)](https://github.com/Brown-University-Library/iip-texts) EpiDoc corpus into a research-oriented [Text-Fabric](https://annotation.github.io/text-fabric/) dataset.

## Status

**Pre-0.1 / working converter and local browser, not yet a released corpus.**
The pinned Brown source can be converted into reproducible native Text-Fabric
data and browsed offline using the standard TF app. There is not yet a
published corpus artifact or a working Agora materializer.

**New researchers:** start with the [executable five-minute quickstart](docs/guides/researcher-quickstart.md)
and the [local browser guide](docs/guides/local-tf-browser.md).

The release target is a native Text-Fabric corpus that:

- preserves IIP textual and editorial semantics as TF nodes/features rather than XML/JSON blobs or semantic sidecars;
- uses **sign slots** with normal **word**, **line**, **textpart**, and **inscription** nodes, following the sign-slot precedent used by ETCBC/DSS where it fits IIP;
- keeps gaps, supplied/uncertain text, choices, expansions, numerals, glyphs, language, source identity, metadata, bibliography, provenance and facsimile information queryable in TF;
- stays compatible with BHSA/DSS/ETCBC conventions where the underlying semantics actually match;
- uses the standard Text-Fabric app/browser instead of a custom web application;
- can be built reproducibly from a pinned Brown IIP source revision;
- exposes a tested third-party materializer contract for Agora without moving converter semantics into Agora.

## Development roadmap

The release work is tracked in GitHub issues:

1. [#2 corpus-wide EpiDoc and licence audit](https://github.com/alexsosn/IIP-TF/issues/2)
2. [#3 freeze the native TF data model](https://github.com/alexsosn/IIP-TF/issues/3)
3. [#4 canonical source parser/IR](https://github.com/alexsosn/IIP-TF/issues/4)
4. [#5 native TF writer](https://github.com/alexsosn/IIP-TF/issues/5)
5. [#6 metadata/bibliography/provenance/facsimiles](https://github.com/alexsosn/IIP-TF/issues/6)
6. [#7 whole-corpus validation and reproducibility](https://github.com/alexsosn/IIP-TF/issues/7)
7. [#8 standard TF app/browser](https://github.com/alexsosn/IIP-TF/issues/8)
8. [#9 researcher-first documentation](https://github.com/alexsosn/IIP-TF/issues/9)
9. [#10 lightweight end-user distribution](https://github.com/alexsosn/IIP-TF/issues/10)
10. [#11 Agora materializer contract](https://github.com/alexsosn/IIP-TF/issues/11)
11. [#12 0.1.0 release gate](https://github.com/alexsosn/IIP-TF/issues/12)

Downstream Agora registration is tracked separately in [Agora #187](https://github.com/alexsosn/Agora/issues/187).

## Architecture

The initial design is documented in `research.md`, `design.md`, and `plan.md`. These are evidence and design documents, not claims that the converter already implements the complete model.

The key rule is that source semantics remain queryable in Text-Fabric. A build report may use JSON for diagnostics, but a researcher must not need a JSON/XML sidecar to recover corpus semantics.

## Licence

Software authored in this repository is MIT licensed. IIP source data and generated corpus data retain the upstream terms and attribution requirements. See `LICENSE_SCOPE.md`; the corpus-wide licence audit in #2 is a release gate.
