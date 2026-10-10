# Browse IIP-TF locally with standard Text-Fabric

This guide describes the **converter repository** workflow. There is no
published versioned Text-Fabric dataset yet: `tf alexsosn/IIP-TF` must **not**
be advertised as a working one-command install. Distribution is tracked in
[#10](https://github.com/alexsosn/IIP-TF/issues/10).

## Build the authenticated corpus

Run these commands at the root of an IIP-TF checkout, using Python 3.11+ and
enough disk/memory for roughly 1.47 million sign slots. The source commit and
its Git subtree are independently checked by the release validator.

```bash
python -m pip install -e '.[dev]'

IIP_REV=0b7dc8358ccdfd0c9391f049da4839fbd91c26e5
mkdir -p upstream-iip
set -o pipefail
curl --fail --location --retry 3 \
  "https://codeload.github.com/Brown-University-Library/iip-texts/tar.gz/$IIP_REV" \
  | tar -xz --strip-components=1 -C upstream-iip

python scripts/validate_pinned_tf.py \
  upstream-iip/epidoc-files \
  build/pinned-tf \
  --revision "$IIP_REV" \
  --converter-commit "$(git rev-parse HEAD)"
```

For safety the validator **rejects occupied output and report directories**;
use fresh locations for subsequent rebuilds. It emits native `.tf` files to
`build/pinned-tf/` and independent JSON/Markdown **build reports** to
`build/pinned-tf-reports/`. Reports are diagnostics, not corpus semantics.

## Open the local browser

From the same repository root:

```bash
python -m tf.browser.start \
  "app:$(pwd)/app" \
  "--locations=$(pwd)/build/pinned-tf" \
  -noweb
```

The TF process prints its localhost address and continues serving requests.
Open that address in your normal browser; terminate the process with Ctrl-C.
`-noweb` only prevents **automatically launching** a GUI browser. It does
**not** disable the local HTTP service. No online corpus download is needed
once the native dataset and app configuration are present.

For Python, the app can wrap an already-loaded core TF API:

```python
from pathlib import Path
from tf.app import use
from tf.fabric import Fabric

root = Path.cwd()
api = Fabric(locations=str(root / "build/pinned-tf"), silent=True).loadAll()
app = use(f"app:{root / 'app'}", api=api, silent="deep")
inscription = app.api.T.nodeFromSection(("abil0001",))
print(app.api.T.text(inscription, fmt="text-orig-full"))
```

The section hierarchy is inscription → textpart → line. The default
`text-orig-full` format selects the **primary** inscription layer. To inspect
other layers, request the appropriate format explicitly:
`text-transcription-full`, `text-diplomatic-full`,
`text-translation-full`, or `text-commentary-full`. The `lang` values in
this development snapshot still have known source-versus-display problems
tracked in [#57](https://github.com/alexsosn/IIP-TF/issues/57).

**Known reading limitations:** some non-primary sections render as empty in
the default format ([#51](https://github.com/alexsosn/IIP-TF/issues/51));
empty `<g ref=.../>` glyph references currently render invisibly
([#58](https://github.com/alexsosn/IIP-TF/issues/58)). For now query their
native markup `kind=glyph` and `ref` features rather than treating an empty
display as an empty inscription. The app does not infer missing text or
normalize undeciphered marks.

Original IIP texts are © their respective owners and supplied under the
source project's terms (CC BY-NC 4.0); see `LICENSE_SCOPE.md`.
