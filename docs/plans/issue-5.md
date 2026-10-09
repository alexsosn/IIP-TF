# Issue #5 plan — native Text-Fabric writer

Research: `docs/research/native-tf-writer.md`

## Research gate

Use direct `tf.fabric.Fabric.save()` from canonical IR. Do not route final IR
back through a source-walking converter.

Two serializer-specific schema clarifications are required:

1. add `point_index` (int) and `point_relation` (before/after) TF node
   features for #43 zero-width semantic points;
2. clarify that `text-layer-full={glyph}{after}` is a literal stored-slot
   view, while selected normalized/source display is provided by the derived
   primary/source/layer-specific features.

No source parsing semantics move into the writer.

## RED

Before production code:

1. a two-reading fixture expects normalized and source-oriented formats to
   select different sign roles;
2. a zero-width semantic point at an interior boundary expects one technical
   oslot plus reconstructable `point_relation`/`point_index`;
3. an empty edition/paragraph expects a technical primary anchor and `empty=1`;
4. an empty-record synthetic anchor loads with three configured section levels
   and no invented textpart/line;
5. semantic edge features round-trip through Text-Fabric;
6. two writes of the same IR expect byte-identical top-level `.tf` files and
   no `@dateWritten` lines;
7. duplicate global canonical keys, mixed feature value types, inconsistent
   source revisions and unexpected empty node types fail closed.

The first RED commit should fail because `iip_tf.tf_writer` does not exist.

## GREEN

Implement:

- deterministic record/sign/node numbering;
- raw + derived slot features;
- node features and writer-derived empty/point features;
- normal `otype`, `oslots`, semantic edge features and `otext`;
- generic provenance metadata;
- `Fabric.save()` serialization;
- deterministic `@dateWritten` normalization;
- Text-Fabric reload validation and binary-cache cleanup;
- `write_tf_corpus(irs, output_dir, converter_commit)` as the stable writer API.

Add a small CLI `convert SOURCE OUTPUT --source-revision ... --converter-commit ...`
that parses sorted top-level non-test XML files into IR and invokes the writer.
The CLI must not silently skip parse failures.

## Full-source gate

Add `.github/workflows/validate-pinned-tf.yml`:

1. fetch exact pinned Brown source;
2. install the exact PR head;
3. parse all 5,535 non-test records;
4. write the complete TF corpus;
5. reload it with Text-Fabric;
6. assert source/node/token accounting already frozen by the IR gate;
7. assert point-node count/reconstruction;
8. assert no `@dateWritten` remains.

## Review

After exact-head ordinary CI and full-source TF validation:

- perform a fresh logically independent adversarial review;
- inspect the actual `.tf` conventions through Text-Fabric's loader, not only
  writer unit tests;
- challenge point anchoring, empty structural anchoring, section navigation,
  display-role selection, edge direction, type metadata and determinism;
- fix every blocker, rerun exact-head gates, and re-review before merge.
