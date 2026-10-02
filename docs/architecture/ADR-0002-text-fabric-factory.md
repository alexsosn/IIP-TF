# ADR-0002 — text-fabric-factory is reference material, not the IIP-TF converter

Status: **Accepted**

Issue: #41.

Research: `docs/research/text-fabric-factory-evaluation.md`.

## Context

Text-Fabric's companion package `text-fabric-factory` (TFF) provides generic
XML/TEI -> TF conversion, schema tooling, and generated app/documentation
support. IIP-TF already has a frozen semantic contract in ADR-0001 and a
TF-independent canonical IR.

The question is whether adopting TFF would remove enough conversion machinery
to justify another dependency and migration boundary.

## Decision

IIP-TF will **not** depend on `text-fabric-factory` for production conversion.

The canonical architecture remains:

`pinned IIP source -> researched repair/preflight -> semantic parser -> canonical IR -> native TF writer`.

TFF may be consulted as implementation/reference material. In particular:

- #5 may evaluate `tf.convert.walker.CV` directly, because IIP-TF already
  depends on Text-Fabric and TFF itself uses that lower-level API;
- #8 may reuse TFF app-generation/documentation ideas without importing its TEI
  conversion semantics;
- TFF's XML-schema tooling and reporting patterns may inform optional
  development utilities, provided they do not become an unexamined build
  dependency.

## Rationale

TFF 1.0.8's generic TEI conventions conflict with ADR-0001 in several
independent ways:

1. Its supported slot granularities are `word`, `token`, and `char`;
   IIP-TF requires `sign` slots whose population excludes ordinary whitespace
   and includes typed zero-width source events.
2. Its vanilla walk creates a TF node named after nearly every TEI element.
   IIP-TF maps source syntax into a small semantic vocabulary such as
   `markup`, `entity`, `bibl_scope`, and `facsimile_surface`.
3. The TFF walk reduces element and attribute QNames to local names. IIP-TF's
   parser intentionally validates namespace identity before semantic mapping.
4. TFF walks `teiHeader` as corpus content and marks generated slots as
   metadata. IIP-TF maps header facts into inscription features and structured
   metadata nodes anchored to source text.
5. TFF's ordinary parse-error path can skip malformed XML and continue. IIP-TF
   requires complete file accounting and applies only exact revision-scoped
   researched repairs to the seven malformed files in the pinned corpus.
6. IIP words come from audited `transcription_segmented` candidates and
   deterministic projection to the chosen primary layer. Generic tokenization
   or treating segmented XML as another text layer is not equivalent.

The TFF hook surface is powerful, but restoring these invariants through hooks
would reproduce the current IIP-specific semantic parser inside a stateful TF
walker. It would not remove the difficult code or preserve the clean IR
serialization boundary.

## Consequences

- Do not add `text-fabric-factory` to `pyproject.toml`.
- Do not make TFF's generated TEI graph an intermediate IIP representation.
- The TF writer stays responsible only for serializing canonical IR; it must
  not regain source-XML interpretation responsibilities.
- A direct `tf.convert.walker` implementation remains allowed if #5 shows it
  makes IR serialization simpler without changing node/slot identities.
- TFF upgrades do not become IIP-TF release blockers.

## Revisit

Reconsider only if TFF adds a namespace-preserving semantic mapping mode that
can define externally supplied slot/event identities and suppress vanilla
element nodes before creation, or if a future IIP-TF schema intentionally
moves toward TFF's element-shaped model.
