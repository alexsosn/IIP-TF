# Issue #30 research — metadata certainty paths

Pinned source: `Brown-University-Library/iip-texts@0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.

The corpus audit already measured four metadata attributes whose path-specific semantics were
not assigned dedicated inscription features in schema 0.1:

- `msItem@cert`: 1 occurrence; `akas0001.xml` has `cert="low"`;
- `origin/date@precision`: 5 occurrences in current `epidoc-files`; observed value is `low`;
- `origin/region@cert`: 2 occurrences; `hebr0001.xml` has `unknown`,
  `jord0001.xml` has `low`;
- `origin/settlement@cert`: 3 occurrences; observed value is `unknown`.

This is not safely representable by the generic node feature `cert`. In particular,
`hebr0001.xml` simultaneously has both `region@cert="unknown"` and
`settlement@cert="unknown"`; the values happen to match there but qualify different claims
and must remain distinguishable.

The correction is additive and does not change warp, node types, sections, textual mappings, or
display semantics.

Frozen path-specific features:

- `genre_cert` ← `msItem@cert`;
- `date_precision` ← origin `date@precision`;
- `region_cert` ← origin `region@cert`;
- `settlement_cert` ← origin `settlement@cert`.

All four are raw string features. No controlled-vocabulary normalization is introduced.
