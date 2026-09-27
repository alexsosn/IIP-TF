# IIP-TF 0.1 plan

Issue #12 is the release gate. The dependency flow is:

```text
#2 source/licence research
          |
          v
#3 schema ADR
          |
          v
#4 parser IR
     |         \
     v          v
#5 TF writer   #6 metadata model
     \          /
      v        v
       #7 full-corpus validation
        |        \
        v         v
 #8 TF app     #9 researcher docs
        \        /
         v      v
          #10 distribution
             |
             v
       #11 Agora materializer
             |
             v
         #12 release gate
```

## Phase 1 — measure before modelling

### #2 Corpus-wide reconnaissance and licence audit

Produce reproducible counts and construct inventories from the pinned Brown source. This is the evidence gate for schema decisions.

### #3 Native TF schema ADR

Freeze slots, node types, features, text formats, anchoring rules, source identity, and compatibility policy using #2 evidence.

## Phase 2 — conversion core

### #4 Typed parser / canonical IR

Parse EpiDoc into a representation that exposes every supported semantic construct explicitly and reports unsupported constructs deterministically.

### #5 TF writer

Serialize the IR to valid deterministic TF, then load it with the supported Text-Fabric release.

### #6 Metadata graph

Preserve research-useful physical, geographical, chronological, bibliographic, provenance, hand, decoration, facsimile and entity information without opaque blobs.

## Phase 3 — whole-corpus truthfulness

### #7 Full-corpus validation

No unexplained partial success. Account for every source record, validate graph integrity and determinism, and run representative content assertions.

## Phase 4 — researcher UX

### #8 Standard TF app/browser

Provide normal Text-Fabric app configuration and browser/API loading.

### #9 Researcher documentation

Write installation, schema, feature reference, query examples, reproducibility, citation/licence guidance, and limitations from the user's perspective.

## Phase 5 — distribution and Agora

### #10 Lightweight distribution

Researchers should not need the full development/source tree merely to load the released corpus.

### #11 Agora materializer

Publish a tested upstream `agora.materializer.json` and execution module. Agora integration stays downstream (Agora #187).

## Phase 6 — release

### #12 0.1.0 gate

Release only after complete-source conversion, app/browser smoke, documentation examples, licence/provenance, deterministic build, materializer integration contract, and independent exact-head review are all satisfied.

## Autonomous work selection

Agents should take the earliest actionable release dependency. If a task is blocked, work on another independent prerequisite rather than speculative post-0.1 features.

Research may create focused issues for source constructs discovered by #2. New work enters the release path only when required for correctness, data preservation, reproducibility, installation/loadability, documentation truthfulness, or licence compliance.
