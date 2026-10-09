# Issue #6 — queryability gate

Research: docs/research/issue-6-native-metadata-queries.md

- RED: add TF API integration tests for scalar metadata, bibliography scopes,
  nested facsimile surfaces, physical metadata, revisions and TF search. The
  existing writer may already pass many tests; first demonstrate the missing
  end-to-end acceptance coverage through tests on real serialized data.
- GREEN: implement only tests/docs/full-source query smoke unless a test
  demonstrates lost source semantics.
- Full-source: reuse the pinned corpus TF job; confirm every expected metadata
  node and relation is reachable through the loaded TF API.
- Independent review: inspect actual pinned source shape, canonical mapping,
  output features and edge directions; challenge false query claims and
  duplicate/flattened child handling.
- Finish only on the exact final head with CI + pinned full-source gates green.
