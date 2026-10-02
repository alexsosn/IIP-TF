# Issue #38 plan — fail closed on metadata prose semantics

## Research gate

Full pinned-source path audit is recorded in `docs/research/metadata-prose.md` and reproducible with `scripts/research_issue38.py`.

## RED

Before production changes, tests require:

- unknown attributes on each mapped prose `p` path to fail;
- an unsupported nested semantic element in metadata prose to fail;
- `foreign@xml:lang` in support prose to fail because the only audited wrapper has no attributes;
- the exact audited `support/p > foreign` shape to continue producing the same support-note text.

## GREEN

Add one metadata-prose extraction helper that validates the element before returning normalized prose. Use it at every current support/condition/layout/origin/hand prose call site. Keep the allowlist path-specific: `foreign` is transparent only under support prose.

## Verification / review

- Ruff, strict MyPy, Pytest green;
- pinned canonical IR remains 5,535/5,535 with frozen node counts and 39,472 segmented token identities;
- exact-head logically independent adversarial review checks that no `itertext()` metadata prose escape hatch remains.
