# Research — mapped metadata prose semantics

Issue: #38.

Pinned Brown IIP revision: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.

`scripts/research_issue38.py` scans all 5,535 non-test records after #15 source preflight. It measures the five metadata prose paths currently consumed via `itertext()` without path-specific validation.

## Results

| Path | Records | `p` elements | Attributes on `p` | Nested elements |
|---|---:|---:|---|---|
| `support/p` | 2,580 | 2,585 | none | one `foreign` |
| `condition/p` | 5,530 | 5,530 | none | none |
| `layout/p` | 5,535 | 5,535 | none | none |
| `origin/p` | 5,369 | 5,369 | none | none |
| `handNote/p` | 3,955 | 3,956 | none | none |

Total audited prose `p` elements: **22,975**. No path has a source attribute on `p`.

The sole nested case is `akld0007.xml`:

`<support><p>This is more <foreign>information</foreign> about the support</p> ...`.

The `foreign` element has no attributes and no nested children. Its visible text is already part of the support-note prose. No other metadata prose path contains inline markup in the pinned corpus.

## Parser consequence

- Metadata prose `p` has an empty allowed-attribute set.
- `condition/p`, `layout/p`, `origin/p`, and `handNote/p` allow no child elements.
- `support/p` allows only the audited transparent `foreign` wrapper.
- The audited `foreign` wrapper has an empty allowed-attribute set and no child elements.
- Any future attribute or other nested element is an unresearched semantic change and must fail closed rather than disappear through `itertext()`.

This is a validation hardening only: it does not change the frozen TF node model or current pinned-source values/counts.
