# Research — fail-closed text-valued metadata semantics

Issue: #38.

Pinned Brown IIP revision:

`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`

The audit in `scripts/research_issue38.py` runs after #15 source preflight and scans all
**5,535 non-test records**. It covers every metadata path whose visible value is currently
obtained from element text rather than from a mapped attribute.

## Metadata prose paragraphs

The five prose paths contain **22,975** `p` elements:

| Path | Records | Elements | Attributes | Children |
|---|---:|---:|---|---|
| `support/p` | 2,580 | 2,585 | none | one `foreign` in one record |
| `condition/p` | 5,530 | 5,530 | none | none |
| `layout/p` | 5,535 | 5,535 | none | none |
| `origin/p` | 5,369 | 5,369 | none | none |
| `handNote/p` | 3,955 | 3,956 | none | none |

The sole nested support case is `akld0007.xml`:

`<p>This is more <foreign>information</foreign> about the support</p>`

The `foreign` wrapper has no attributes and no children. It is therefore an audited transparent
wrapper for support-note text, not a general metadata-inline vocabulary.

## Other text-valued metadata

The expanded audit found these source shapes:

- dimensions: `height` 5,324, `width` 5,252, `depth` 4,978; only the already-mapped
  `atLeast`/`atMost` attributes occur; no children;
- origin `date`: 5,533; mapped `notBefore`, `notAfter`, `period`, and rare
  `precision`; no children;
- origin `region`: 5,535; only two `cert` attributes; no children;
- origin `geogName`: 5,534, always mapped `type`; no children;
- origin `geogFeat`: 4,360, always mapped `type`; no children;
- settlement `geo`: 470, no attributes or children;
- provenance `placeName`: 5,535, no attributes or children;
- `biblScope`: 7,598; only mapped `unit` and `n`; no children;
- decoration `ab` and `locus`: 7,995 each, no attributes or children;
- facsimile `note`: 57, no attributes or children;
- revision `change`: 18,690; only mapped `when`, `when-custom`, and `who`; no children.

Facsimile descriptions are the other audited nested exception:

- 5,644 `desc` elements in 5,514 records;
- no attributes on `desc`;
- exactly 97 descendant/direct-child `persName` elements in 59 records;
- every such `persName` has the mapped `role` attribute and no children.

Thus `desc > persName@role` is the only source-supported nested facsimile text shape.

## Parser contract

All mapped metadata text extraction is fail-closed:

1. validate the text-bearing element's attributes against its audited allowlist;
2. reject unmeasured child elements;
3. validate attributes and childlessness of any explicitly allowed transparent child;
4. only then normalize visible text.

The only transparent nested forms in schema 0.1 are:

- `support/p > foreign`, with no attributes or children;
- `surface/desc > persName@role`, with no nested children.

Everything else is leaf text. A future source revision adding semantics to these paths must fail
closed until researched rather than silently disappearing through `itertext()`.

This hardening changes no current TF node model or pinned-source values.


## Namespace boundary

Adversarial review found that a local-name-only allowlist is insufficient: an unresearched
namespace can otherwise alias an allowed TEI element or attribute name.

Metadata validation therefore treats namespaces as semantic:

- element names are accepted as TEI names only when their namespace is the TEI namespace;
- the XML namespace is recognized explicitly for supported `xml:id` / `xml:lang` attributes;
- elements outside the TEI namespace, including explicitly unnamespaced descendants, fail
  closed instead of being reduced to an allowed local name;
- attributes in namespaces other than the XML namespace fail closed instead of being reduced to
  an allowed local name. Ordinary unqualified TEI attributes remain matched by their audited
  names.

The pinned source adds no additional metadata namespaces, so this changes no current values.
