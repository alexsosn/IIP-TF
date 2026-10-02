# Issue #38 plan — fail closed on text-valued metadata semantics

## Research gate

`docs/research/metadata-prose.md` and `scripts/research_issue38.py` cover every metadata path
whose value is derived from element text, across all 5,535 non-test pinned records.

## RED gates

RED tests are committed before each production broadening.

First RED slice:
- unknown attributes on support/condition/layout/origin/hand prose `p`;
- unsupported nested prose semantics;
- unresearched attributes on the sole audited support `foreign` wrapper.

Second RED slice, triggered by adversarial review:
- unsupported children in dimensions, origin date/region, bibliography scope, and revision change;
- unresearched provenance/decorative attributes;
- unknown facsimile-description child;
- nested content inside the audited credit `persName`;
- preserve the valid `desc > persName role=...` credit shape.

## GREEN

Use one validated metadata-text extractor. The extractor validates the current element, checks a
path-specific direct-child allowlist, validates any allowed transparent child, requires it to be
childless, then returns normalized text.

Only two paths permit children:
- support `p`: `foreign`;
- facsimile `desc`: `persName`.

All other audited text-valued metadata elements are leaf nodes.

## Verification

- Ruff and strict MyPy green;
- all focused tests green;
- pinned full-source canonical IR remains 5,535/5,535 with frozen node/token counts;
- research workflow remains reproducible;
- exact-head logically independent adversarial review checks for any remaining raw `itertext()`
  call site reachable from mapped metadata.
