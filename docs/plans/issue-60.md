# Issue #60 — durable source failure accounting

## Research
Pinned script `scripts/validate_pinned_tf.py` authenticates the entire Brown
EpiDoc source Git tree, excludes only `aaTestFile.xml`, then parses 5,535
records and builds/reloads/reproduces native TF before any report is written.
Any exception between the report-directory guard and final success path leaves
no source accounting. The workflow currently skips its report upload if build
fails; `release_gate.write_build_reports` writes both files directly.

## TDD gates
1. RED entrypoint fixtures: two real source file paths plus excluded sentinel,
   monkeypatch only the corpus sizes and expensive parser. Fail the second
   parser call; assert nonzero exit and JSON/Markdown report with separate
   parsed, converted, failed with stage/type, and unprocessed source files.
2. RED failure during TF writer: report all inputs parsed but zero records
   counted as converted. Never include exception text / potentially raw XML.
3. GREEN narrowly-scoped failure ledger for parse, TF write and late build/
   validation failures. Keep source-authentication and output guards fail closed.
   Do not fabricate TF nodes or loosen cardinality checks.
4. Harden report publication with atomic per-file replace and a fresh report
   directory guard. On failures *before* report initialization the workflow
   must tolerate absence of reports.
5. Mark artifact upload `if: always()` and missing-report tolerance
   without marking the build successful. Test CI and actual pinned builds.
6. Logically independent adversarial review of error injection, stage
   correctness, path safety, partial-write atomicity and unchanged success gate.

Native corpus semantics remain unchanged. Reports are diagnostics, not TF sidecars.
