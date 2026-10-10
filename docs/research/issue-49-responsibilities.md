# Issue #49 — source responsibility provenance research

Status: pinned full-source research audit completed; native modeling under test.
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

## Whole-corpus measurement (GitHub Actions run 38039970693)

Ran `scripts/research_issue49_responsibilities.py` on all **5,535** repaired,
pinned source files. The audit workflow succeeded.

| Observed construct | Occurrences |
| --- | ---: |
| `titleStmt/title` | 5,535 |
| `titleStmt/respStmt` | 5,536 |
| Records with two `respStmt` | 1 |
| `respStmt/persName` | 3,449 |
| `respStmt/name` | 2,087 |
| `titleStmt/principal/persName` (separate construct) | 1 |
| `resp=Creator` | 2,086 |
| `resp=Prinicipal Investigator` (source typo) | 3,445 |
| `resp=Principal Investigator` | 3 |
| `resp=Project Manager` / `Technical Oversight` | 1 each |
| Explicit `publicationStmt/authority` (`Brown University`) | 2,052 |
| Unexpanded `xi:include` | 3,483 |
| `publicationStmt/idno` | 5,535 |
| Explicit `publicationStmt/availability` | 3 |

All observed `respStmt` have exactly one `resp` and one `name` or
`persName`, with no unexpected children. Agent names may lack `xml:id`;
any identifier is local to its XML record. The 3,483 XInclude hrefs are
the identical source URI
`http://cds.library.brown.edu/projects/iip/include_publicationStmt.xml`.
Each include has an `xi:fallback` diagnostic; it is not an explicit
publication-authority or licence assertion.

Publication `idno` can be empty, as in `achz0001.xml`. The 3 explicit
`availability` nodes use `status="free"` and nested licence text, ref and
paragraph constructs. `akld0019.xml` also contains the sole
`titleStmt/principal`, plus two `respStmt` records with distinct roles.
Its source title is inscription-specific, not the uniform project title.

## Native model decision

- Keep the unique per-record `titleStmt/title` as a scalar `source_title`
  on `inscription` and an explicit `publication_authority` only where
  the authority is present in that record.
- Retain each `respStmt` or exceptional `principal` as a distinct,
  technical-slot-anchored `responsibility` TF node with `parent` and
  `in_inscription` edges. `responsibility_role` is raw source text;
  `responsibility_construct` and `agent_tag` distinguish TEI structures.
  Never merge same-name or same-`xml:id` agents across files.
- Retain every `idno` as a `publication_id` node, including empty
  identifiers, and every XInclude as `publication_include` with literal
  href, diagnostic fallback text, and unresolved status.
- Retain explicit availability and licence via typed parented TF nodes,
  with child `publication_reference`/`publication_paragraph` nodes.
  Preserve direct original `ref` targets and source order in source keys.
- Reject unsupported source child/attribute shapes; never hide them inside
  an XML or JSON payload. These new metadata nodes do not generate additional
  visible `sign` slots. The pinned validator freezes real counts after a
  complete canonical IR/TF round-trip.
