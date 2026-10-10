# Issue #9 — native researcher quickstart, executable first slice

## Research
The shipped `docs/guides/query-native-metadata.md` has snippets that assume `TF_DIR`
was previously defined; `docs/reference/schema-0.1.md` is a schema
summary, not a corpus-checked feature inventory. The successful #61 native
app already loads the entire authenticated Brown corpus in
`scripts/validate_pinned_app.py`, so use that *same* API for researcher
examples instead of a third costly full-corpus load.

The actual native Text-Fabric schema has sign slots, inscription/textpart/line
sections, original-vs-translation formats, `markup` source annotations,
semantic `parent/cites` edges, source metadata on `inscription`, and
native TF feature headers containing source revision and CC BY-NC 4.0. The
pinned source examples were inspected directly: `abil0001.xml` includes
`gap/supplied/unclear`, `caes0260.xml` includes `abbr/ex`,
`masa0286.xml` includes `g ref=phoen-gaml`, and `chor0001.xml`
contains ordinary visible reading text.

## Research-plan-TDD-test-review

1. RED unit tests against a genuine minimal EpiDoc -> IR -> TF fixture for
   section navigation, exact-ID search, original and translation,
   native markup, source metadata and feature inventory.
2. RED negative tests: an unknown inscription or nonexisting feature in
   a documented query must be an explicit error, not an empty success.
3. GREEN create `iip_tf.researcher_queries` functions + `python -m` entrypoint,
   ensuring CLI JSON is a *printable result*, not a TF semantic sidecar.
4. Add `docs/guides/researcher-quickstart.md` covering setup, first query,
   sections, layer reading, metadata, editorial limits, feature discovery,
   source revision, credit and noncommercial licence. All Python code
   examples reference executable functions.
5. Reuse the already-loaded pinned browser app API in
   `scripts/validate_pinned_app.py` to verify actual example IDs and
   editorial source features. The expensive corpus rebuild is shared with
   #7/#8 gates.
6. Exact-head Ruff, MyPy, pytest and authenticated 5,535-record gate;
   separate, logically-independent adversarial review on actual source
   and loaded TF; only then merge. #9 stays open for complete manual,
   exhaustive reference and more scholarly worked queries.

Do not guess canonical languages (#52–#55), glyph substitutions (#58), or
URLs (#10), and do not interpret JSON diagnostics as corpus semantics.
