# Issue #8 — standard Text-Fabric app and browser

## Research (2026-10-10)

- #7 finished at merge `52fb804bf75a01db33254b0f136751b714090ae0`: pinned TF is built reproducibly from 5,535 Brown records. This converter repository deliberately does **not** check in the 157 TF feature files.
- Text-Fabric 13 advanced apps use `app/config.yaml` for optional settings and `app.py` only for custom display functions: https://annotation.github.io/text-fabric/tf/about/apps.html and https://annotation.github.io/text-fabric/tf/advanced/settings.html.
- A local advanced API can wrap a separately loaded core API without downloading anything: `use("app:/absolute/path/to/app", api=api)`; the core API comes from `Fabric(locations=generated_tf_dir).loadAll()` per https://annotation.github.io/text-fabric/tf/about/usefunc.html.
- The `tf.browser.start` CLI recognises `app:full/path/to/app`, `data:full/path/to/data/version`, `--locations` and `-noweb`. An actual working combined local-app + local-data browser command must be established by test; we must **not** claim the remote `tf alexsosn/IIP-TF` auto-download path works until #10 publishes a versioned corpus.
- Native TF sections are `inscription,textpart,line`, and the source text uses the `text-orig-full` display format; other layer formats (translation, commentary) are available. App must not pretend all signs belong to the same language; special glyph references remain synthetic.

## Planned research → TDD → implementation → test gates

1. RED smoke: small synthetic EpiDoc record converted to native TF; wrap the loaded TF `api` with `tf.app.use("app:<local-app-path>", api=api)`, require working inscription navigation, search and readable `plain()`. Test config keys/types are recognised by TF 13, and no network needed.
2. GREEN minimal `app/config.yaml`: corpus provenance, main reading format, display defaults, appropriate section/line labels, graphical hints without speculative links. Avoid app Python unless essential for verified formatting.
3. RED browser smoke via documented CLI with generated TF. Launch a local headless server, wait for a verifiable health endpoint, and terminate it deterministically. Fail closed on unsupported invocation rather than handwaving.
4. GREEN researcher-facing setup guide with commands that work on clean local data; representative Greek/Aramaic/Hebrew and gap/editorial examples.
5. Pinned full-source app load/section navigation and browser test, exact-head CI, independently skeptical source/code review. Do not merge until all checks pass.

### Release boundary

`app/config.yaml` is a display config, not a corpus semantic sidecar. No XML/JSON transformations or new TF content are stored in the app. TF data packaging / download is tracked by #10, so browser command claims must distinguish locally generated data from published versioned data.

## CI-observed RED and correction (2026-10-10)

- Exact-head run 38063447435: 3 browser fixture tests fail after native TF successfully loads. Run 38063447436: the full pinned 5,535-record, 157-feature reproducibility build succeeds, then `tf.app.use` fails in `tf.advanced.links.linksApi` at `"/".join(components)` because `app.context.version` is `None` (third component) when app provenance omits a data version.
- Source check: TF 13.1's `linksApi` creates a local path with `version` unconditionally for `app:`-style paths. The unversioned local TF directory is legitimate; configure an **explicit empty string**, `provenanceSpec.version: ''`, which prevents the TypeError without inventing a published version or activating remote-data discovery.
- RED evidence is the actual three failing fixture tests plus full-corpus browser gate; the config test now requires this documented empty version and the production browser tests must go green. Do not disable link generation or replace the standard TF server.
