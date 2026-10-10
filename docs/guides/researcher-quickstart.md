# First five minutes with IIP-TF: researcher quickstart

This is an executable, researcher-oriented guide for the **native**
[Text-Fabric](https://annotation.github.io/text-fabric/) corpus derived from
Brown's Inscriptions of Israel/Palestine (IIP). No released auto-downloadable
IIP-TF corpus exists yet (distribution issue
[#10](https://github.com/alexsosn/IIP-TF/issues/10)).
Run the commands from the **IIP-TF converter repository root**.

## 1. Obtain and authenticate the corpus

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
print(api.S.search("inscription inscription_id=abil0001"))
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

For more worked native metadata/edge queries, including bibliography,
Pleiades source references, physical dimensions, facsimile credits and
contributor/provenance records, see
[Querying IIP metadata](query-native-metadata.md) and the
[0.1 native schema reference](../reference/schema-0.1.md).

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
the current browser does not fully visualize supplied/uncertain source
apparatus (#65), non-primary display (#51) and empty referenced glyphs (#58).
Do not infer an absence of reading, person identity or dating merely from a
missing feature or empty display. Current IIP public deep links are not assumed
to be stable. Researcher distribution and Agora integration are tracked in
[#10](https://github.com/alexsosn/IIP-TF/issues/10) and
[#11](https://github.com/alexsosn/IIP-TF/issues/11).
