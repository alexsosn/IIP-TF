# Issue #24 plan — typed textual IR

## Research

See `docs/research/text-ir-parser.md`. The design is constrained by schema 0.1 and the
merged #15 source preflight.

## RED-first slices

1. IR types are immutable/typed, deterministic, and contain no raw XML payload.
2. Basic Greek transcription creates code-point signs, implicit textpart, paragraph and lines.
3. Gaps/lb/handShift/empty glyph references produce one synthetic source-position sign each.
4. Nested supplied/unclear/choice/expansion markup preserves hierarchy and reading roles.
5. Translation entities preserve spans and mapped attributes.
6. Diplomatic fallback and empty-anchor primary selection follow schema 0.1.
7. Explicit textparts and paragraph language inheritance remain layer-aware.
8. Unsupported textual elements/attributes fail deterministically.
9. Source repair is invoked before XML parsing.

## Implementation

- `src/iip_tf/ir.py`: canonical immutable graph types and invariants;
- `src/iip_tf/text_parser.py`: namespace-aware EpiDoc textual parser;
- no Text-Fabric writer dependency;
- no header metadata graph yet;
- no segmented projection yet.

The parser may load the frozen JSON schema to validate support tables, but normal parse behavior
must be deterministic without network access.

## Verification

Focused fixtures cover source patterns measured by the corpus audit. After unit GREEN, add a
read-only pinned-source textual coverage job that runs repaired files through the #24 textual
parser and reports every unsupported native textual construct.

A #24 PR is final only when focused and full-source textual tests pass on the exact head and a
logically independent adversarial review finds no silent-loss/ordering/whitespace blocker.
