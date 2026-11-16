# Issue #62 — native shared publication identity and citation links

## Research (verified inputs, no guessed corrections)

The Brown source at pinned revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, Zotero export Git blob `38f7c4d7c8c24756a0023e3e77c7ed6e02b8786d`, has **767 actual TEI biblStruct entries, 762 IIP source keys on 761 keyed entries, six unkeyed works**, including one source-authored two-ID work (`IIP-001`, `IIP-694`). The upstream export is stale relative to the EpiDoc records: unknown/malformed references cannot be corrected by inference. Source-target matcher introduced in #119 permits only `IIP-[0-9]+` optionally followed by literal `.xml`.

Targeted source inventory over all 767 TEI works: 861 `author` elements, 77 `editor` elements; seven author/editor elements use a single `name` child instead of forename/surname; 754 works have an explicit date, 13 none, no multiple `date` tags seen. Work `IIP-119` actually has title *A Catalogue of Jewish Ossuaries in the Collections of the State of Israel*, author `L.Y. Rahmani`, editor `Ayala Sussmann`, and `date=1994`. Names, source date text, analytic title vs monograph title, and source keys must remain distinct, with ordered repeated agent nodes.

Existing Text-Fabric IIP writer models inscription-scoped `bibl` nodes, all anchored by technical nonempty `oslots`. Source TF model explicitly supports nodes linked to arbitrary sets of slots (including discontinuous slots) and lexeme-like work nodes that span *their occurrences*: https://annotation.github.io/text-fabric/tf/about/datamodel.html . Do not designate one arbitrary inscription as a global publication owner. Represent a **shared cited publication** with `oslots` equal to the exact union of technical sign anchors of its referencing `bibl` nodes. Keep an explicit `bibl → publication` edge as the real semantic relation, never infer authorship from slot embedding. A publication may span several inscriptions and have no `in_inscription` owner. No separate XML/JSON semantic sidecar.

## Decisions and scope

- One publication node **per cited source work**, not one per alias/citation, with deterministic source ordinal and first attested key. Each explicit source key becomes a separate `publication_key` child linked by native `parent`, and each repeatable source author/editor becomes a separate ordered `publication_agent` child with role and source-derived name components.
- Source titles, imprint date and publisher/place are separate parsed-source features on `publication`, not canonical bibliographic corrections. No inferred year, author identity matching, normalizations, reprints or zero-padding. Use `publication_title` for the source analytic title if nonempty, else monograph title, while preserving both originals separately.
- Existing inscription `bibl.target`, `ptr_type`, `bibl_scope`, `cites`, signs, slot order, and original TF text formats remain unchanged.
- Unsupported/unrecognized targets produce **no publication edge**, and a reproducible diagnostic count. No fabricated missing works or cross-document correction.
- Unpinned standalone EpiDoc-only conversions remain possible; pinned full Brown builds and Agora managed adapter must require/authenticate the exact corresponding Zotero bytes.

## Research → plan → RED → implement → adversarial review gates

1. Commit RED-first *native Fabric real reload* tests demonstrating cross-inscription shared work identity; untyped pointers; two-key alias collapsing into one work; repeated authors/editors with preserved order; unknown/padded-malformed references refusing links; deterministic reversed IR input; unchanged original target and sign text.
2. Implement source agent/date extraction and native graph projection through existing writer with optional authenticated authority, plus README, native schema and an ADR-0001 amendment.
3. Add CLI full-source auto-discovery and explicit override, pinned source validation and full-source linked/unresolved census. Require a source-backed Rahmani 1994 query through **native TF** without reading external XML at query time. Update Agora input contract if the full source now requires bibliography authority.
4. Exact-head full CI, authenticated source, native 5,535-inscription independent double build and browser, raw and freshly compiled Context-Fabric parity, plus actual conversion canaries. A high feature-count or node-count drift fails rather than passing opportunistically.
5. Perform logically independent adversarial review grounded in the final diff, real source and completed gates before finalization.

*If the TF/CF engines reject multi-inscription discontinuous publication spans, stop and revise the ADR based on the actual failure; never silently anchor a shared work to an arbitrary inscription or truncate source.* This PR closes only the graph part of #62 when verified. User-facing query docs / unreconciled source anomalies and the 0.1 release remain separately gated.
