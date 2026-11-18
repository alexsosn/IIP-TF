# Standalone researcher distribution (issue #10)

**Status: the 0.1.0rc1 corpus DATA prerelease is a versioned public download.
Final IIP-TF 0.1.0 has not been released.** This snapshot is a plain
native Text-Fabric dataset and browser app, not a converter wheel or
an automatically hosted corpus. Do not use `tf alexsosn/IIP-TF` as an
automatic install command.

## Download the versioned corpus and verify its checksum

Download the three public assets from the
[corpus-data-0.1.0rc1 prerelease](https://github.com/alexsosn/IIP-TF/releases/tag/corpus-data-0.1.0rc1).
No GitHub login, repository checkout, IIP source XML, or converter installation
should be needed:

```bash
curl --fail --location --remote-name \
  "https://github.com/alexsosn/IIP-TF/releases/download/corpus-data-0.1.0rc1/iip-tf-corpus.tar.gz"
curl --fail --location --remote-name \
  "https://github.com/alexsosn/IIP-TF/releases/download/corpus-data-0.1.0rc1/iip-tf-corpus.tar.gz.sha256"
curl --fail --location --remote-name \
  "https://github.com/alexsosn/IIP-TF/releases/download/corpus-data-0.1.0rc1/corpus-provenance.json"

sha256sum -c iip-tf-corpus.tar.gz.sha256
```

The checksum command must report `iip-tf-corpus.tar.gz: OK`. Stop if it
does not match. On systems without `sha256sum`, compare the archive SHA-256
using your platform's SHA-256 command or Python before extraction.

The separately downloaded `corpus-provenance.json` records the full
authenticated Brown source revision
`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`,
the exact converter commit, the archive digest and the 5,535-record
count. The archive's TF feature headers independently retain source and
converter provenance. Cite the underlying Brown IIP
[DOI 10.26300/pz1d-st89](https://doi.org/10.26300/pz1d-st89)
and the original scholarly editions in addition to this conversion.
Data remain **CC BY-NC 4.0**; bundled app/software is MIT.

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

The temporary `iip-tf-researcher-candidate` artifact in GitHub Actions is
for CI review only. Use the versioned public prerelease linked above for
downloads, not a short-lived Actions artifact. The public publishing workflow
requires an independently downloaded byte-for-byte checksum, fresh Text-Fabric
installation, exact provenance and browser/search smoke on a separate runner.
See [issue #10](https://github.com/alexsosn/IIP-TF/issues/10) for acceptance
evidence and [issue #12](https://github.com/alexsosn/IIP-TF/issues/12)
for the final 0.1.0 release gate.
