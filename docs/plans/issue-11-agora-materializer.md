# Issue #11 — root-preserving Agora materializer, source and browser fidelity

## Authenticated research (2026-10-20)

Agora main `2c94c7c024bd88b7df403cbd4ab30074367cecc5` uses materializer-plugin.schema.json v1 and `scripts/agora_materialize.py`. Required declaration: plugin identity, git/user-local acquisition, directory input globs, python module args restricted to `{source}`, `{output}`, `{source_revision}`, network deny, and required output paths. Host provides an **existing empty staging directory** and user-local sources may have empty revision; it separately hashes the source. Host validates actual Git revision and output paths and runs code in its own network-denied sandbox.

Brown pinned source: `Brown-University-Library/iip-texts@0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`. The existing converter accepts **`epidoc-files/`** and discovers `include_taxonomies.xml` and `data-keep/persons.xml` in its **parent directory**. A manifest with `subpath=epidoc-files` would silently lose authenticated taxonomy normalization and real person links. The materializer must acquire the **Brown repository root** and reject absent sibling authority files, then invoke the existing conversion CLI on its child `epidoc-files/` without copying/reimplementing EpiDoc semantics. Full (not sparse) Git acquisition is safest for a first correctness slice; actual minimal sparse checkout patterns are future optimization and must first satisfy Agora's anchored sparse pattern constraints.

IIP's local Text-Fabric app consists of `app/app.py`, `app/config.yaml`, and `app/static/display.css`. Existing wheel configuration only packages `src/`; a materializer installed by Agora cannot assume the repo-level `app/` remains accessible. Bundle the **same** browser app files as `iip_tf` package data, assert byte-for-byte synchronization against the source app, and export them unchanged to local materialized artifact. Avoid a reduced browser config that would drop source-critical editorial renderer semantics.

Existing CLI requires `--converter-commit`, but Agora installs code without .git metadata and passes no converter Git SHA. Never fabricate a Git commit. Use an explicitly identified deterministic **`sha256:<hex>` package-source fingerprint** in that field; Agora's own receipt binds plugin Git SHA and its managed code identity separately. For user-local no-revision inputs, use documented `unversioned-local` rather than a false Brown source Git hash. The root archive still must contain both authority files.

## Scope

1. `agora.materializer.json` declares immutable Brown Git root plus user-local Brown root, forbids symlinks, and requires all three source components.
2. `iip_tf.agora` runs the unchanged public converter in Agora's empty staging root, generates `tf/` + original browser app + provenance-only `conversion-summary.json`, with no network use or fake source texts. Reject occupied/symlink output and missing sources before touching output.
3. Wheel bundles the complete browser app, asserted identical to root version. Existing local standalone `iip-tf convert` behavior remains unchanged; no dependency on Agora runtime from IIP-TF.
4. RED-first tests require an actual EpiDoc→IR→native TF reload with taxonomy+person register, source-provenance preservation, unversioned-local acknowledgement, byte-identical browser app and no network; invalid input must not silently degrade. Manifest must be validated against pinned **actual Agora host** schema/semantics in a separate integration workflow.
5. Exact-head Ruff, strict MyPy, pytest, immutable Agora-host contract smoke and pinned complete native TF gate; final logically independent adversarial review before merging. If any gate fails, retain draft. Defer expensive live git source acquisition and Agora downstream registry install/publish to #187, after reviewed upstream ref and 0.1 release.

## Constraints

Software MIT; upstream IIP EpiDoc and derived TF remain CC BY-NC 4.0 with edition-specific attribution. No images or source corpus binaries are bundled. Local output is not an authorized unrestricted distributable dataset. Agora owns acquisition, sandbox/host, installation trust and artifact publication; IIP-TF does not fork those components.

## Adversarial source-accounting amendment (2026-10-20)

Review of `inventory_source_files` found `aaTestFile.xml` is excluded only when the converter receives Brown's authenticated pinned source revision. Agora user-local acquisition supplies an empty `{source_revision}` for downloaded tarballs without .git, so the initial adapter would misclassify that test fixture as an inscription. Two new RED-first tests at commits `48e0465`/`1d0051b` fail on the production path (CI #39389601694: 2 specific pytest failures; Ruff/MyPy green). Fix: authenticate all three consumed Brown source components when revision is empty; if exact, pass true pinned revision to the unchanged converter; otherwise refuse the known `aaTestFile.xml` in unverified inputs. Do not invent a revision for other local content. This does not broaden the schema/IR.
