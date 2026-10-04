# Research — zero-span semantic nodes and TF anchoring

Issue: #43. Blocks #5.

## Pinned-corpus evidence

Audit source: `scripts/research_issue43_zero_spans.py`.

Pinned Brown revision:
`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.

The audit parsed all 5,535 non-test records through the current canonical parser.

It found **11,476 IR nodes with an empty semantic span** across 3,606 records:

| node type | empty-span nodes |
| --- | ---: |
| edition | 5,710 |
| paragraph | 5,717 |
| markup | 49 |

The structural empties are expected source fidelity, not point annotations:

- empty editions are explicitly preserved by schema 0.1;
- empty paragraphs/ab blocks are explicitly preserved by `textual_blocks.preserve_empty_blocks`;
- they do not encode a location *between* signs.

The 49 empty markup nodes are semantically different. Their kinds are:

| markup kind | count |
| --- | ---: |
| supplied | 16 |
| del | 11 |
| unclear | 11 |
| abbr | 4 |
| ex | 4 |
| choice | 2 |
| lemma | 1 |

Fifteen are projected from `transcription_segmented`; nine carry zero-atom
token identity:

- `caes0250-3`
- `caes0330-2`
- `caes0440-1`
- `mare0188-3`
- `zoor0356-22`
- `zoor0446-4`
- `zoor0446-8`
- `zoor0446-12`
- `zoor0446-15`

The earlier full-source accounting is therefore explained exactly:
39,472 selected segmented token identities =
39,463 word nodes + 9 zero-atom token identities retained on markup nodes.

## Real source shapes

The zero-atom tokens are not parser inventions.

Examples at the pinned revision include:

- `caes0250`: native `<supplied reason="undefined"/>`, and segmented token
  `caes0250-3` containing the same empty supplied element;
- `caes0330`: the same pattern for `caes0330-2`;
- `caes0440`: native transcription starts with `<unclear/>`, followed by
  `<lb/>`; segmented token `caes0440-1` is `<w><unclear/></w>`;
- `mare0188`: native transcription ends after a gap with empty
  `<supplied reason="lost"/>`; segmented token `mare0188-3` preserves it;
- `zoor0356` and `zoor0446` contain corresponding empty editorial markup
  in native and segmented transcription.

Other empty markup is nested inside non-empty tokens, for example empty
`abbr` or `ex` children. The pinned `idum0375` stale segmented apparatus
also yields one empty projected `lemma` node after projection onto the newer
native transcription.

## Why the current IR is insufficient

For an inline source element, the text parser knows the exact sign-boundary
offset when it starts the element:

`start = len(builder.signs)`.

If the element contributes no signs, `IRNode.sign_keys == ()` currently
throws that offset away.

The same loss occurs in segmented projection. `_AnnotationSpec` retains atom
start/end offsets, but `emit_annotations()` collapses an annotation to
`()` when no projected primary position survives.

After that loss a TF writer cannot distinguish, for example:

- a point before the first sign;
- a point between two signs;
- a point after the last sign;
- an empty structural container that has no point semantics at all.

## Text-Fabric constraint

Text-Fabric 13.1.x cannot represent an ordinary non-slot node with an empty
`oslots` mapping:

- `Fabric.save()` validates that every non-slot node is mapped;
- the `oslots` reader assumes every non-slot node is present;
- an empty target specification is rejected.

Therefore a native TF corpus must give every non-slot node at least one
technical slot anchor. That technical anchor must not be confused with the
semantic extent of a zero-width node.

## Model decision

Add an IR-only optional field:

`IRNode.point_index: int | None`

Semantics:

- it is a **boundary offset** in the record-local `InscriptionIR.signs`
  sequence;
- valid range is `0..len(signs)`;
- `0` means before the first sign;
- `len(signs)` means after the last sign;
- an interior value `k` means between `signs[k - 1]` and `signs[k]`;
- a node with `point_index != None` must have `sign_keys == ()`;
- empty structural containers have `sign_keys == ()` and
  `point_index == None`.

This preserves semantics without fabricating source text or introducing a
second slot layer.

### Native inline parser

For empty inline semantic nodes (markup, and future empty entities if observed),
store the already-known `start` offset as `point_index`.

Existing source-critical events such as `gap`, `lb`, `space`,
`handShift`, `milestone`, empty `g`, and `figure` already receive a
synthetic sign and therefore remain ordinary non-empty spans. They do not need
`point_index`.

### Segmented projection

Projection must preserve a deterministic point rather than merely emitting
`()`.

Two cases exist.

1. **Zero-atom token / annotation with a matching native empty markup point.**
   Prefer the native point of the same semantic kind inside the projected
   target paragraph and within the monotonic bounds set by neighboring token
   matches. Source features that carry semantics (for example reason/rend)
   participate in compatibility. Exactly one candidate is required.

2. **Empty projected annotation inside a non-empty token.**
   Derive the boundary from the token match's neighboring mapped atoms. If the
   left and right evidence disagree because unmatched primary material lies
   between them, fail closed rather than guess.

The nine pinned zero-atom token identities are expected to resolve through
case 1. The stale `idum0375` apparatus is the main case 2 adversarial target.

## TF encoding contract for #5

#43 preserves the semantic point in canonical IR. #5 must then encode it in
standard TF without adding text slots:

- a non-empty node maps to its semantic `sign_keys` as usual;
- an empty structural node maps to the inscription's established technical
  anchor and retains/derives `empty=1`;
- a point node maps technically to one adjacent sign and emits an explicit
  point relation feature (before/after the anchor) so the semantic boundary is
  reconstructable;
- the writer must never replace `()` with an arbitrary neighboring slot.

The exact TF feature names belong to #5 because they are serializer-facing.
The canonical invariant is the `point_index`, not a particular TF anchoring
convention.

## Rejected alternatives

### Add one synthetic sign for every empty semantic node

Rejected. It changes the frozen slot population for annotation-only segmented
data and can introduce multiple artificial slots at one source boundary.
Synthetic signs remain reserved for source-critical events and the one
empty-record anchor.

### Anchor every empty node to the first inscription sign

Valid only for technical containment of empty structural/metadata nodes.
For semantic point markup it destroys the source position.

### Infer a neighbor only in the writer

Rejected because the writer sees the already-lossy IR and cannot recover the
original boundary reliably.

## Scope refinement

The research result narrows #43 to preserving point semantics in canonical IR
and projection. The final TF anchoring/load-round-trip assertion belongs to #5,
where the writer exists; #5 is updated to require it. This avoids implementing
a throwaway serializer solely to close the blocker.
