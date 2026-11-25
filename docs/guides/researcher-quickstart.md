# First five minutes with IIP-TF: researcher quickstart

This is an executable, researcher-oriented guide for the **native**
[Text-Fabric](https://annotation.github.io/text-fabric/) corpus derived from
Brown's Inscriptions of Israel/Palestine (IIP). The versioned **corpus-data-0.1.0rc2** public data prerelease contains all
5,535 inscriptions and the local TF browser with Original EpiDoc links.
**Final IIP-TF 0.1.0 has not been released.**

- To begin searching, browsing and following original source links without cloning the converter,
  start with the [standalone download and installation guide](researcher-distribution.md).
  It covers checksum verification, Text-Fabric-only installation and a native search.
- To reproduce the corpus or run the converter-specific `iip_tf.researcher_queries`
  examples below, follow the source-build route in this quickstart. Run these
  commands from the **IIP-TF converter repository root** with its dependencies
  installed as described in the local browser guide.

## 1. Build the authenticated corpus

Use Python 3.11+, sufficient free storage and RAM for 1,466,387 Unicode-sign
slots, and the pinned upstream source revision. Copy/paste the fully specified
build procedure in [Build the authenticated corpus](local-tf-browser.md#build-the-authenticated-corpus).
It downloads the upstream Brown XML, authenticates the exact source Git tree,
converts all 5,535 real inscriptions to native `.tf` features, independently
builds a second corpus and checks every feature's SHA-256 byte hash.

The result is `build/pinned-tf/`. The accompanying
`build/pinned-tf-reports/` files are **diagnostic build reports, not semantic
metadata required by Text-Fabric**. The validator rejects nonempty build output
directories; do not overwrite previous work.

## 2. Run verified examples

After building, from the same checkout:

```bash
python -m iip_tf.researcher_queries build/pinned-tf \
  abil0001 chor0001 caes0260 masa0286
```

This returns printable JSON with exact-inscription-ID search results, recorded
source IDs and source files, original/translation text, editorial phenomena,
reference glyph identifiers, and a **discovered inventory of native node/edge
features**. JSON is the *output of a query*, never an auxiliary corpus store.
These four examples run against the actual pinned corpus in the full
validation workflow, not just in synthetic documentation.

Research examples, **without silently inventing text**:

- `abil0001` has source `supplied`, `gap` and `unclear` marks. Check
  `markup_kinds` to discover them; default text rendering alone does not
  distinguish all editorial uncertainty yet ([#65](https://github.com/alexsosn/IIP-TF/issues/65)).
- `chor0001` provides an ordinary visible original-text reading.
- `caes0260` has abbreviation/expansion `abbr` and `ex` annotations.
  Plain text alone does not reproduce the critical apparatus.
- `masa0286` has `glyph` annotations with `phoen-gaml` and other source
  references. Missing graphic substitutions are *not* invented
  ([#58](https://github.com/alexsosn/IIP-TF/issues/58)).

For any other source inscription, pass its **exact** file-stem ID instead of
the four examples. An unknown ID exits with an error, not an empty apparently
successful result. Feature names are checked against the loaded Text-Fabric
data, rather than assumed from this page.

## 3. Make the same queries in Python

```python
from pathlib import Path

from tf.fabric import Fabric
from iip_tf.researcher_queries import inspect_corpus, require_native_features

root = Path.cwd()
api = Fabric(locations=str(root / "build/pinned-tf"), silent=True).loadAll()
assert api is not None
require_native_features(api, ("inscription_id", "source_file", "primary_layer"))

results = inspect_corpus(api, ("abil0001", "caes0260"))
for record in results["records"]:
    print(record["inscription_id"], record["primary_text"])
    print("Editorial markup:", record["markup_counts"])
    print("Translation:", record["translation_text"])

# Direct native section navigation and precise Text-Fabric search:
inscription = api.T.nodeFromSection(("abil0001",))
assert inscription is not None
print(api.F.source_file.v(inscription))
print(tuple(api.S.search("inscription inscription_id=abil0001")))
```

These operations retrieve data directly from **native `.tf` features**:
the script calls `T.nodeFromSection`, `T.text`, `S.search`, `F`,
`Fs`, `L.d`, and `TF.explore`, rather than parsing an XML or JSON sidecar.
`inspect_corpus` also reports `metadata_node_counts` for the `bibl`,
`bibl_scope`, `entity`, `image`, `facsimile_surface`,
`responsibility` and publication node types.

## 4. Understand the hierarchy

```text
inscription (source record, section 1)
└── textpart (source edition/layer, section 2)
    └── line (section 3)
        └── sign (Text-Fabric slot: visible code point or zero-width source event)
```

`word` nodes come only from validated IIP segmentation. `markup` nodes
preserve inline EpiDoc structures, including reconstructed `supplied` signs,
unknown-extent `gap`, `unclear` letters and textual choices. Bibliography,
physical metadata, image links and attribution are separate **native TF nodes
and edges**; no opaque XML/JSON metadata sidecars are used.

The `text-orig-full` format selects the **primary** transcription or
diplomatic reading. `text-translation-full`, `text-diplomatic-full`,
`text-transcription-full` and `text-commentary-full` select other layers.
An empty default reading on a non-primary textpart does **not** imply the source
layer is absent ([#51](https://github.com/alexsosn/IIP-TF/issues/51)).
`text-layer-full` is a literal stored-slot view and may show competing
editorial branches; do not interpret it as a vetted critical edition.

Empty source glyph references are visible in the **new opt-in**
`text-orig-unicode-full` and the standard browser's
`text-section-normalized-unicode-full`. A reviewed one-to-one Phoenician
character uses its real Unicode scalar (e.g. `phoen-gaml` → 𐤂,
`phoen-delt` → 𐤃 in `masa0286`); otherwise the source label
`((ref))` is shown instead of inventing a symbol. All 153 observed source
refs have a reviewed policy. The original `glyph` and the default native
`text-orig-full` still preserve the empty synthetic positions. For example:

```python
from tf.fabric import Fabric
api = Fabric(locations="PATH/TO/TF").loadAll()
node = api.T.nodeFromSection(("masa0286",))
print(api.T.text(node, fmt="text-orig-unicode-full"))
```

That output contains the reviewed Phoenician codepoints; source spacing can
occur between them. Query the original markup `ref` for source provenance,
not the derived glyph display. The complete mapped/fallback table and cautions
are in [the native schema reference](../reference/schema-0.1.md).

For more worked native metadata/edge queries, including bibliography,
Pleiades source references, physical dimensions, facsimile credits and
contributor/provenance records, see
[Querying IIP metadata](query-native-metadata.md) and the
[0.1 native schema reference](../reference/schema-0.1.md).

To inspect classification vocabularies and **all six source taxonomy labels**,
including writing techniques not stored as an inscription feature, use
`iip-tf taxonomy-catalog` with the authenticated Brown `include_taxonomies.xml`;
see [the source taxonomy guide](pinned-taxonomy-audit.md#browse-all-six-source-taxonomies-issue-100).
This read-only lookup never guesses a `parent` or `is_a` relationship from
a dotted category identifier.

## Query record-level source language variants (issue #52)

IIP's inscription-level `main_lang` preserves the original EpiDoc
`textLang@mainLang` spelling. On the pinned 5,535-inscription native corpus
the **source values** `he` and `heb` occur on **405** and **4**
inscription nodes, respectively. An exact query for `main_lang=heb`
therefore finds only four of these 409 Hebrew-labeled records. The source
audit counts *textLang declarations* separately and reports 475 `he`
instances; do not conflate that XML occurrence count with native
inscription-node counts.

Use the public, source-preserving native query helper for the **record-level**
language aliases whose equivalence is supported by ISO language codes:

```python
from tf.fabric import Fabric
from iip_tf.researcher_queries import find_inscriptions_by_main_language

api = Fabric(locations="build/pinned-tf", silent=True).loadAll(silent=True)
hebrew = find_inscriptions_by_main_language(api, "heb")
print(len(hebrew))  # 409 on the verified Brown pin
print([api.F.inscription_id.v(n) for n in hebrew[:5]])
# The original EpiDoc main_lang values remain distinct and queryable:
print({api.F.main_lang.v(n) for n in hebrew})  # {'he', 'heb'}
```

The helper supports only `heb` → `he`/`heb`, `lat` →
`la`/`lat`, and `kat` → `geo`/`Geo`. It returns a sorted
tuple of **native inscription node IDs**, using exact indexed source-value
queries; source attributes, TF data, and node ownership are unmodified.
On the authenticated pinned **native inscription** nodes, the Latin
query retrieves 284 `la` and **zero** `lat`; `lat` occurs in the
source's token-level `xml:lang` audit, but not in the pinned
`F.main_lang` record-level feature. The Georgian query retrieves
three `geo` and one `Geo` native inscriptions. Both source-code
count sets are independently enforced by pinned CI. The equivalent
explicit Hebrew native query is
`set(api.F.main_lang.s("he")) | set(api.F.main_lang.s("heb"))`. 

**Do not apply these aliases blindly to sign/word `lang`.** In IIP an
inherited `xml:lang="heb"` on an Aramaic inscription can denote its
Hebrew-script presentation, and #54/#92 are deliberately conservative
about assigning a linguistic identity. `other_langs` may contain
space-separated source codes and requires token-aware filtering; it is
not handled by this exact record-level helper. Unclassified/mixed source
values such as `Other`, `x-unknown` and `arc-Grek` are not
silently mapped. A separate materialized ISO-derived language feature was
**not introduced**, pending evidence-based resolution of the remaining
script-vs-language cases.

See the [source language audit](../research/iip-corpus-audit.md#languages)
for the original EpiDoc occurrence distributions, and the
[Library of Congress ISO language codes](https://www.loc.gov/standards/iso639-2/php/English_list.php)
for Hebrew, Latin and Georgian identifiers.

## 5. Browse, provenance, and responsible citation

To browse or search through standard Text-Fabric's local web interface, follow
[Open the local browser](local-tf-browser.md#open-the-local-browser). The
command starts a localhost service; `-noweb` suppresses automatic GUI
launch, not the HTTP server.

The source is pinned to Brown IIP commit
`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`; the validator checks
upstream `epidoc-files/` Git tree
`4445c4878873227c73ead5e8b94f9e3487c28c3b`. The native
Text-Fabric feature metadata contains source revision, IIP DOI
[10.26300/pz1d-st89](https://doi.org/10.26300/pz1d-st89), and converter
provenance.

**The upstream inscription corpus and generated Text-Fabric data retain
CC BY-NC 4.0** and source-edition/contributor attribution obligations.
IIP-TF converter code alone is MIT; these are different licence scopes.
See [licence and source attribution](../../LICENSE_SCOPE.md) and cite the
actual inscriptions/editions, not merely the converter. Image binaries are not
redistributed by this build; metadata may retain only their links and credits.

**Limitations:** language codes are *source raw values*, not verified language
or writing-system normalizations
([#52–#57](https://github.com/alexsosn/IIP-TF/issues/57));
source-critical editorial apparatus remains only partially visualized
(#65), and some non-primary display issues remain (#51). Glyph references
now have explicit reviewed Unicode/fallback display (#58).
Do not infer an absence of reading, person identity or dating merely from a
missing feature or empty display. The Original EpiDoc browser link targets the authenticated Brown Git revision;
other IIP public deep links are not assumed to be stable. The published data
prerelease is documented in the [distribution guide](researcher-distribution.md).
Managed Agora integration remains tracked in
[#11](https://github.com/alexsosn/IIP-TF/issues/11).

## Native personal names and register data

The pinned full Brown source includes `data-keep/persons.xml`. After an authenticated build, names referring to this source file have **native** person register nodes and directed `person_ref` links. Example, a registered Jewish female's name (the register's `faith` is literal, not a proof of inscription-wide classification):

```python
from tf.fabric import Fabric
api = Fabric(locations="build/pinned-tf", silent=True).loadAll(silent=True)
assert api
for entity in api.F.otype.s("entity"):
    for person in api.E.person_ref.f(entity):
        if api.F.sex.v(person) != "2":
            continue
        for inscription in api.L.u(entity, otype="inscription"):
            if "jewish" in (api.F.religion.v(inscription) or "").split():
                print(api.F.inscription_id.v(inscription), api.F.person_name.v(person))
```

This query finds source-register sex code `2` in inscriptions with the `jewish` taxonomy ID among their classifications (including fully-resolved multi-IDREF fields) from the Brown EpiDoc `msItem/@ana` source (e.g. pinned `beth0002`, Hannah). The register's personal `faith` is separate: do not conflate an individual's faith with an inscription's classification. Native `person` nodes are per-register-entry and per-inscription; identical names are not global identities. Missing `faith` or `sex` remains missing, and unregistered or contributor references do not produce a graph link. Outside the full IIP checkout, provide `iip-tf convert --persons-register /path/to/persons.xml ...` explicitly, or expect a corpus without those links. No external web lookup is needed to query the native nodes.

**Classification provenance:** In the full Brown build, `F.religion` holds source-taxonomy ID `jewish`, while `F.religion_original` retains the exact EpiDoc `#jewish`. Standalone EpiDoc-only conversions without `include_taxonomies.xml` retain the old raw feature semantics and should not be treated as taxonomy-normalized.
