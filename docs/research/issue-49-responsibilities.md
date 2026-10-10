# Issue #49 — source responsibility provenance research

Status: research gate in progress.
Pinned source: `Brown-University-Library/iip-texts@0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.

## Initial primary-source observations

- `idum0375.xml`, `akld0007.xml`, and `masa0779.xml` contain
  `teiHeader/fileDesc/titleStmt/respStmt/resp` = `Prinicipal Investigator`
  (retain the original typo) and a `persName xml:id="MS"` identifying
  Michael Satlow.
- `mgha0001.xml` uses `resp=Creator` and a `name xml:id="MS"` instead.
- `mgha0001.xml` also has `publicationStmt/authority` = Brown University.
- Other records contain publication XInclude references, which are raw
  external-resource references, *not* expanded source statements in the
  pinned XML. They must not be silently converted into inferred licence data.
- Existing native `revision` nodes preserve revisionDesc/change who/when,
  but neither `titleStmt/respStmt` nor source publication authority is mapped
  by the metadata parser.

These observations are supported by source XML at the exact pinned revision.
Their corpus-wide frequencies and additional variants remain to be measured
before choosing a schema.

## Research script

`scripts/research_issue49_responsibilities.py` audits the full pinned source
through the existing revision-scoped preflight repair. It reports counts and
distinct child/attribute shapes for titleStmt responsibilities and publication
authority/include, plus representative role/name pairs and anomalous cases.

## Design constraints

- Repeatable responsibility records must remain repeatable TF nodes or a
  rigorously documented shared project-level metadata feature if *identical*
  and strictly global across the measured source.
- The original role text, agent label and source identifier must remain
  separate. Do not globally resolve `xml:id="MS"` across files by guess.
- Source schema must validate unexpected child/attribute shapes fail-closed.
- Do not introduce raw XML/JSON/sidecar semantic payloads.
- Keep revisionDesc/change semantics and source permissions separate.

No design/implementation decision is final until the full-corpus audit runs.
