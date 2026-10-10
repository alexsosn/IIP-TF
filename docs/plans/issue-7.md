# Issue #7 — reproducible whole-corpus release acceptance

## Research (pinned evidence, 2026-10-10)
- Brown source `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5` has exactly 5,536 `epidoc-files/*.xml` files; 5,535 release records and the one intentional test fixture `aaTestFile.xml`. The old `"test" in path.name.lower()` exclusion policy was too broad.
- On merged main `214db4c`, canonical IR/TF totals are 5,535 inscriptions, 1,466,387 sign slots, 322,860 semantic nodes and 409,785 semantic edges; the source-provenance audit and 162 tests are green.
- `cli._convert` has no source-file accounting or retained report. `validate_pinned_tf` freezes counts but rebuilds only once and prints transient JSON. `tf_writer.write_tf_corpus` sorts record/node keys and removes volatile `@dateWritten`, yet no independent bytewise reproducibility proof exists.
- The TF representation must remain native. Reports are build artifacts, never sidecar semantics.

## Plan / TDD gates
1. RED tests: exact-source exclusion (do not skip unrelated files with 'test' in names), deterministic ordered input ledger (converted/excluded/failed), failure must not be a successful build, no overwritten last-known-good report.
2. GREEN explicit directory inventory and machine/human-readable manifest with exact source pin, converter SHA, counts, file identities and reasons.
3. RED tests: reproducible .tf filename set and bytewise digest comparison in distinct output directories, handling extra/missing/modified feature files, ignoring .tf cache directories.
4. GREEN independent fresh parse/write pipeline twice from the pinned Brown corpus, every .tf feature SHA-256 identical; persist Markdown/JSON build report and hashed manifest as Actions artifacts.
5. Confirm orphan-free oslots/edges, record identity uniqueness, full metadata/section integrity and no unaccounted source losses.
6. Final logically independent, skeptical review on exact-head code and real data; merge after CI, pinned IR and full two-build TF checks green.

## Failure policy
Unsupported source records block release; explicit exclusion is allowed only for the enumerated pinned `aaTestFile.xml`. No broad substring heuristic, no guessed substitutions. Any differing .tf file hash, missing feature, unsupported node, malformed source, or output provenance mismatch blocks release.
