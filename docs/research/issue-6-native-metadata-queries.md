# Research — issue #6 native metadata queryability

Baseline: main f08baafc9d09c1f7556d6c57fea9b4e644a1208e.
Pinned Brown source: 0b7dc8358ccdfd0c9391f049da4839fbd91c26e5.

## What is already implemented

#25, #34/#37 and #38 implemented and hardened native metadata parsing in
`src/iip_tf/metadata_parser.py`. #5 implemented `Fabric.save()` serialization
of every typed IR node/feature/edge, without opaque XML/JSON semantic sidecars.

The pinned build now loads through Text-Fabric with 5,535 inscription nodes,
7,596 bibliography nodes, 7,598 bibliography scopes, 8,658 dimension nodes,
5,535 hands, 7,996 decorations, 5,667 facsimile surfaces, 6,738 image nodes,
18,690 revision nodes and 1,516 support notes. The writer round-trips all
380,645 semantic edges, including 18,011 `cites` edges and 238,889 `parent`
edges. These are source-derived full-corpus counts from #45.

Existing parser tests verify representative source shapes and fail-closed
handling, but stop at canonical IR; they do not prove a researcher can query the
*written* dataset with Text-Fabric APIs.

## Acceptance gap

Issue #6 requires representative native TF queries for:
- numeric + raw dates, periods, places and Pleiades identifiers;
- repeated physical dimensions, hands, decorations and support notes;
- bibliography references, scopes and `cites` edges;
- image URLs, credits and nested facsimile hierarchy;
- revision provenance and transcription entities;
- search via standard TF engine, not just Python dictionary inspection.

This can be closed by integration tests and worked examples; no new converter
data model or generic data sidecar is justified unless a query exposes actual
semantic loss.

## Test strategy

1. Reuse source-like EpiDoc fixtures from `tests/test_metadata_parser.py`,
   serialize them with `write_tf_corpus`, and assert `F`, `E`, `L`, `T`,
   and `S.search` results. Tests must specifically check edge direction and
   repeated child multiplicity.
2. Add a pinned full-source metadata smoke to the existing native TF validation
   path: assert each of the known node types exists after TF reload and
   expected metadata edge relations are queryable.
3. Write concise researcher examples and limitations based only on observed
   feature names/relations.

No production semantic change is planned unless RED tests reveal a genuine
loss, in which case research/new issues must precede a fix.
