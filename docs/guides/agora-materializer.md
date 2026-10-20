# Build IIP-TF locally via the Agora materializer

**Status:** pre-0.1 development contract; not yet registered in Agora and not a
published corpus artifact. Downstream registration is [Agora #187](https://github.com/alexsosn/Agora/issues/187)
after upstream [#11](https://github.com/alexsosn/IIP-TF/issues/11)
and [#12](https://github.com/alexsosn/IIP-TF/issues/12) acceptance.

## Source contract

The manifest at `agora.materializer.json` declares two source options:

- **Pinned Git:** Brown University Library `iip-texts` at
  `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, acquired at the repository
  **root** (not the `epidoc-files/` subdirectory).
- **User-local:** a researcher-provided copy of the same directory structure.
  A non-Git local folder has `source_revision=unversioned-local`, explicitly
  **not** an authenticated Brown commit.

The following paths are required together:
`epidoc-files/*.xml`, `include_taxonomies.xml`, and
`data-keep/persons.xml`. The sibling controlled taxonomy and person register
are essential to preserve the current converter's native metadata and
person-linking behavior. Supplying only `epidoc-files/` would silently change
its scientific content and is rejected. The manifest uses a complete Git
checkout initially; smaller acquisition patterns require separate proof of
equivalent source coverage.

For the pinned revision, the adapter independently checks the real EpiDoc Git
tree, the taxonomy Git blob, and the person-register Git blob **before**
conversion. With another revision it uses the user's file contents and retains
the supplied revision without claiming to authenticate it. Agora separately
records the acquired tree digest.

## Execute standalone (same producer entry point as Agora)

The module does not contact the network. After installing the converter
(`python -m pip install -e '.[dev]'`) and obtaining the upstream source:

```bash
mkdir -p build/agora-staging
python -m iip_tf.agora \
  upstream-iip \
  build/agora-staging \
  --source-revision 0b7dc8358ccdfd0c9391f049da4839fbd91c26e5
```

The staging root must already exist, be empty and not be a symlink. The module
writes **`tf/`** (native Text-Fabric features), **`app/`** (the complete
standard IIP-TF browser configuration, custom renderer and CSS), and
**`conversion-summary.json`** (diagnostic/provenance, not a semantic sidecar).

To browse the output with the standard TF browser:

```bash
python -m tf.browser.start \
  "app:$(pwd)/build/agora-staging/app" \
  "--locations=$(pwd)/build/agora-staging/tf" \
  -noweb
```

The browser's source-critical editorial overlays remain distinct from native
source glyphs. The normal `tf.fabric.Fabric` API can load the `tf/` folder
without the conversion summary or original source tree.

The adapter calls the **existing standalone `iip-tf convert` command**, with
source revision and a deterministic `sha256:<...>` digest of installed converter
and browser source files in the existing TF `converterCommit` metadata field.
The digest is explicitly **software content identity**, not a forged Git commit.
Agora's approved installation receipt binds the immutable plugin Git ref
separately. The output summary stores only stable relative paths; Agora decides
when and where to publish the staging artifact.

## Trust, licensing and limitations

Installing any Agora third-party Python materializer runs package/build code
and requires explicit approval in Agora. Execution is network-denied by the
host; source acquisition happens before execution and remains an Agora
responsibility. The manifest does not itself cause automatic installation or
registration, and IIP-TF does not import Agora at runtime.

IIP-TF converter software is MIT; original and generated IIP texts are governed
by Brown IIP's **CC BY-NC 4.0** project terms and source-edition attribution
(DOI [10.26300/pz1d-st89](https://doi.org/10.26300/pz1d-st89)).
The adapter does not bundle Brown XML or images, and local generated artifacts
must not be redistributed without following applicable data terms.

The contract and wheel are checked against an immutable real Agora host at
`2c94c7c024bd88b7df403cbd4ab30074367cecc5`; the IIP tests convert and
reload real TEI-shaped fixture records with taxonomy/person authority paths.
Full Git-acquisition, installed registered-host sandbox execution, distribution,
and release smoke checks remain separate gates under downstream Agora #187
and IIP-TF #12.
