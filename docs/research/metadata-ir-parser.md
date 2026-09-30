# Research — canonical IIP metadata IR

Issue: #25, child of #4.

## Frozen contract

Schema 0.1 places one-to-one record metadata on the `inscription` node and preserves
repeatable/structured metadata as native nodes:

- `bibl` + repeatable `bibl_scope`;
- `hand` + child `dimension`;
- inscription-level `dimension`;
- `decoration`;
- `facsimile_surface` + child `image`;
- direct `image` children of the inscription when `graphic` is directly under `facsimile`;
- `revision`.

Metadata nodes reuse a primary/technical sign anchor only because Text-Fabric requires an
oslot anchor. Semantic ownership is explicit with `in_inscription`; direct nested source
structure also uses `parent`.

## Measured cardinality

Pinned non-test parsed source before #15 repair measured maxima:

- bibliography entries: 48/record;
- bibliography scopes: repeat independently of bibl count;
- hand notes: 1/record in the pinned corpus;
- decorations: 20/record;
- facsimile surfaces: 8/record;
- graphics: 9/record;
- revision changes: 10/record.

Repeatable source structures must never be overwritten into a scalar.

## Scalar record metadata

Measured source paths:

- `textLang/@mainLang`, `@otherLangs`;
- `msItem/@class` → raw genre; `msItem/@ana` → raw religion;
- `objectDesc/@ana` → raw object type;
- `supportDesc/@ana` (and the one audited `support/@ana` fallback) → raw material;
- `condition/@ana` + textual `p`;
- `layout/@columns`, `@writtenLines` + textual `p`;
- origin `date/@notBefore`, `@notAfter`, `@period` + text;
- origin `region`, `settlement` + `@ref`, `geogName[@type=site]`,
  `geogFeat[@type=locus]`, `geo`, and origin `p`;
- provenance `placeName` text.

Raw values remain strings. Lossless integer derivatives may be additional features; they never
replace source strings.

If a scalar path yields multiple distinct non-empty values in one record, parsing fails with a
cardinality diagnostic instead of choosing first/last.

## Dimensions

Every `dimensions` element is a `dimension` node.

Surface/object dimensions preserve `type`, `extent`, `unit`, `quantity`,
`atLeast`/`atMost` and child height/width/depth raw strings and child bounds.
Hand-letter dimensions are parented to their `hand` node.

## Bibliography and citations

Every `bibl` is a node; its `ptr` target/type are scalar only because corpus validation
must reject a bibl containing multiple ptr children under schema 0.1. Every `biblScope`
is a child node preserving text, unit, and n.

After bibl nodes exist, textual nodes whose raw `source_ana` or entity `ana` contains a
local token matching `bibl@xml:id` receive a `cites` edge. Unresolved ana values remain raw;
taxonomy/external references are not guessed into bibliography edges.

## Facsimiles

Measured facsimile surface contains `desc`, `graphic`, optional `note`, and in 97 cases
explicit `persName@role` nested in desc.

- surface description is preserved as normalized full desc text;
- surface note is preserved separately;
- each graphic becomes an image node with raw URL;
- an explicit `persName@role` supplies image `credit` and `credit_role` for graphics on
  that surface;
- plain desc text is **not** heuristically reclassified as a credit;
- direct graphics under facsimile are parented directly to the inscription;
- image bytes are never loaded/copied.

## Revision history

Every `revisionDesc/change` becomes a revision node preserving `when`, `when-custom`,
`who`, and normalized description.

## Strictness boundary

#25 parses the schema-0.1 metadata scopes above. Taxonomy declarations, title/respStmt,
publication boilerplate, XInclude/fallback content, profileDesc, and template summary blocks are
not corpus metadata nodes in schema 0.1 and remain explicitly outside this mapping.

Unknown children/attributes inside a mapped metadata structure are release-blocking unless the
frozen schema explicitly permits them. No raw XML fallback exists.
