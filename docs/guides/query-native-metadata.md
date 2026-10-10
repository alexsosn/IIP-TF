# Querying IIP metadata with Text-Fabric

The native corpus exposes EpiDoc-derived metadata as normal Text-Fabric node
features and unvalued edge features. No metadata XML, JSON blob or sidecar
needs to be decoded to issue these queries.

Initialize the standard local TF API (point `TF_DIR` at a generated or
installed corpus):

```python
from tf.fabric import Fabric

api = Fabric(locations=TF_DIR, silent="deep").loadAll(silent="deep")
F, E, L, S = api.F, api.E, api.L, api.S
```

## Inscription-level dates, periods and places

```python
# A feature index over all records with this exact stored region value:
inscriptions = F.region.s("Judaea")
for inscription in inscriptions:
    print(
        F.inscription_id.v(inscription),
        F.date_not_before.v(inscription),   # original string, e.g. "-0010"
        F.date_not_before_int.v(inscription),  # optional lossless numeric year
        F.period_ref.v(inscription),
        F.settlement.v(inscription),
        F.settlement_ref.v(inscription),    # original Pleiades/source reference
    )

# Equivalent single-node TF search over the region feature:
hits = S.search("inscription region=Judaea")
```

Raw dates, certainty and place references are not overwritten by derived
numeric values. Missing numeric derivatives remain absent rather than guessed.

## Repeatable physical and editorial metadata

```python
for dimension in F.otype.s("dimension"):
    if F.dimension_type.v(dimension) != "letter":
        continue
    # A dimension can belong to a hand or to the inscription.
    parent = E.parent.f(dimension)
    print(
        parent,
        F.height.v(dimension),
        F.height_min.v(dimension),
        F.height_max.v(dimension),
        F.dimension_unit.v(dimension),
    )

for support_note in F.otype.s("support_note"):
    print(E.parent.f(support_note), F.note.v(support_note))

for revision in F.otype.s("revision"):
    print(F.when.v(revision), F.who.v(revision), F.description.v(revision))
```

Keep repeated records as nodes: multiple support paragraphs, bibliography
scopes, dimensions, decorations and revisions cannot be assumed to collapse
into one string or one source occurrence.

## Bibliography and citations

```python
for bibl in F.otype.s("bibl"):
    source_reference = F.target.v(bibl)
    scopes = E.parent.t(bibl)  # direct semantic children
    scopes = [n for n in scopes if F.otype.v(n) == "bibl_scope"]
    print(source_reference, [(F.scope.v(n), F.scope_unit.v(n)) for n in scopes])

for edition in F.otype.s("edition"):
    for bibl in E.cites.f(edition):
        print(F.inscription_id.v(L.u(edition, otype="inscription")[0]), F.target.v(bibl))
```

`cites` edges resolve only researched local bibliography identities. An
unresolved raw source `ana` remains in its source feature; do not equate
absence of a resolved edge with absence of a source reference.

## Facsimiles, image credits and hierarchy

```python
for image in F.otype.s("image"):
    parent = E.parent.f(image)
    print(F.url.v(image), F.credit.v(image), F.credit_role.v(image), parent)

for surface in F.otype.s("facsimile_surface"):
    parent = E.parent.f(surface)
    print(F.description.v(surface), F.otype.v(parent[0]) if parent else None)
```

Images contain links/credits only; binaries are not bundled. A surface can be
nested under another surface, and `parent` preserves that relationship.
`in_inscription` provides semantic ownership of metadata and provenance nodes
whose `oslots` spans are purely technical.

## Named entities

```python
for entity in F.otype.s("entity"):
    print(F.entity_kind.v(entity), F.ref.v(entity), L.d(entity, otype="sign"))
```

The displayed sign span and editorial markup remain queryable, including
translation-layer entities and zero-width point semantics. These are
source-derived entities, not inferred entity linking or ontology assertions.

## Provenance and tests

Feature headers expose source commit, DOI, CC BY-NC 4.0 data licence,
converter version/commit and schema version.

The query operations above are exercised on a complete EpiDoc -> IR -> TF
integration fixture by `tests/test_native_metadata_queries.py`.
`scripts/validate_pinned_tf.py` additionally checks metadata structures and
edge direction on the entire pinned Brown source.

This corpus does **not** claim every inscription has every metadata property.
Missing source fields remain missing; raw language/period/place vocabulary is
not silently standardized.

## Source contributor and publication provenance (issue #49)

Header statements are separate native nodes; same `xml:id` in different
inscriptions **does not imply a linked person**.

```python
for responsibility in F.otype.s("responsibility"):
    owners = E.parent.f(responsibility)
    print(
        F.responsibility_construct.v(responsibility),  # respStmt or principal
        F.responsibility_role.v(responsibility),       # literal role, typo retained
        F.agent_tag.v(responsibility),                 # name or persName
        F.agent_name.v(responsibility),
        F.agent_source_id.v(responsibility),           # local to this XML file
        owners,
    )

for inscription in F.otype.s("inscription"):
    print(
        F.source_title.v(inscription),
        F.publication_authority.v(inscription),  # only explicit TEI authority
    )

for include in F.otype.s("publication_include"):
    print(
        F.include_href.v(include),
        F.include_fallback_text.v(include),
        F.include_resolved.v(include),  # "0" = unexpanded, not resolved
    )

for publication_id in F.otype.s("publication_id"):
    # An empty idno still has a native node.
    print(
        F.publication_id.v(publication_id),
        F.publication_id_type.v(publication_id),
    )

for licence in F.otype.s("publication_licence"):
    descendants = E.parent.t(licence)
    print(F.licence_text.v(licence), descendants)
```

Source-explicit publication licence/availability is modeled independently
from corpus-level generated-data licence provenance stored in TF headers.
An XInclude pointer's fallback diagnostic is not evidence that external
publication statements were successfully resolved.
