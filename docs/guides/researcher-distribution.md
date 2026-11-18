# Standalone researcher distribution (issue #10)

**Status: candidate packaging under review; no official IIP-TF 0.1.0
corpus release has been published.** The documented local
[build from Brown's source](local-tf-browser.md) remains available.
Do not use `tf alexsosn/IIP-TF` as an automatic install command.

## What a researcher receives

The `iip-tf-corpus.tar.gz` bundle contains:

- `tf/*.tf`: the complete native corpus, with source and converter provenance
  in TF feature headers. The internal metadata covers readings, editorial
  evidence, persons, taxonomy classifications, bibliography and related links.
- `app/app.py`, `app/config.yaml` and `app/static/display.css`: the same
  standard local Text-Fabric browser app tested against Brown's source.
- `START_HERE.txt`: self-contained installation, navigation and query commands.
- `LICENSE_SCOPE.md` and `LICENSE`: upstream data attribution/CC BY-NC 4.0
  versus locally bundled MIT software, respectively.

No Brown XML checkout, converter package, original images or JSON semantic
sidecars are needed for a researcher to read this artifact. The package is a
data archive, not a Python wheel. It does not modify Text-Fabric itself.

## Install and browse from the downloaded archive

Requirements: Python 3.11 or newer, Text-Fabric 13.1.x and sufficient disk
space and RAM to load approximately 1.47 million sign slots. The commands
below assume the archive file has been obtained and that the working directory
contains `iip-tf-corpus.tar.gz`.

```bash
mkdir iip-tf-data
tar -xzf iip-tf-corpus.tar.gz -C iip-tf-data
cd iip-tf-data
python -m pip install 'text-fabric>=13.1,<14'

python -m tf.browser.start \
  "app:$(pwd)/app" \
  "--locations=$(pwd)/tf" \
  -noweb
```

The standard TF server prints a localhost URL. Open it in your browser and
stop it with Ctrl-C. There is no remote IIP-TF service involved.

Run a corpus query **without cloning the IIP-TF converter**:

```python
from tf.fabric import Fabric

api = Fabric(locations="tf", silent=True).loadAll()
assert api is not None
print(len(api.F.otype.s("inscription")))  # 5535 on authenticated pin
n = api.T.nodeFromSection(("chor0001",))
print(api.T.text(n, fmt="text-orig-full"))
print(tuple(api.S.search("inscription inscription_id=chor0001")))
```

Be careful when citing inscriptions: source `text-orig-full` is a primary
reading; the browser's section-normalized format can show other layers.
Editorial badges and source-label glyph fallbacks are explanatory display
annotations, not additional source letters. Consult the
[researcher quickstart](researcher-quickstart.md), the
[native feature schema](../reference/schema-0.1.md) and
[licence scope](../../LICENSE_SCOPE.md).

## How release maintainers produce and accept an archive

The exact pinned `validate-pinned-tf` workflow already runs full source
accounting, twice-built identical TF features, raw/compiled Context-Fabric
parity, source-aware researcher queries and the real browser. The archive
build reuses those validated `.tf` files:

```bash
mkdir -p build/researcher-dist
python scripts/build_researcher_archive.py \
  build/pinned-tf \
  build/pinned-tf-reports/iip-corpus-report.json \
  build/researcher-dist/iip-tf-corpus.tar.gz
```

The packager rejects absent/unverified source accounting, changed or missing
feature bytes, incomplete warps, symlinks and occupied destinations. It does
not build another corpus or modify source interpretation. The same pipeline
extracts the archive into a different directory, installs Text-Fabric in an
isolated Python virtual environment **without `iip_tf`**, and checks native
section navigation, indexed search, source reading and actual local Flask
homepage/passage routes. Two archives built from the same input have identical
bytes. Any failure blocks candidate upload.

A successful Actions run may temporarily expose the
`iip-tf-researcher-candidate` artifact (GitHub Actions downloads wrap the
`.tar.gz` file in a zip). The ephemeral CI artifact is for acceptance and
review, **not** a persistent versioned data release or managed Agora install.
Issue [#10](https://github.com/alexsosn/IIP-TF/issues/10) remains open until a
public immutable release artifact and separate-machine download/load check are
verified. See the final [0.1.0 release gate](https://github.com/alexsosn/IIP-TF/issues/12).
