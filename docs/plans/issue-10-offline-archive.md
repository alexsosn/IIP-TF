# Issue #10 — offline researcher corpus archive and extracted-copy smoke

## Research (2026-11-18)

- The authenticated current `main` (`b6c72ac89c92dd3033affe9a73338cc2aef86462`) already passes all six source/native/Context-Fabric/Agora CI workflows. The full native gate produces `build/pinned-tf/*.tf` and a successful `build/pinned-tf-reports/iip-corpus-report.json` with a `tf_feature_hashes` inventory after two identical conversions.
- `app/app.py` imports only the normal Text-Fabric advanced app (not `iip_tf`); `app/config.yaml` intentionally specifies an unversioned local corpus and `app/static/display.css` is required for editorial presentation.
- The existing local browser command needs only the generated `.tf` directory and app, but the published instructions require researchers to clone IIP-TF and download Brown XML. #10 specifically requires an independent data installation and clean-machine load. No release or distributed data artifact currently exists.
- Source TF data are CC BY-NC 4.0, while converter software is MIT. Keep `LICENSE_SCOPE.md` inside any redistributed archive, plus the upstream IIP DOI and exact source revision. No XML or image binaries.
- The current full native gate reuses one validated build for browser and raw/compiled Context-Fabric tests. Reuse this artifact instead of building the corpus a third time. GitHub Actions artifacts are **temporary CI candidates**, not an immutable published release.

## Plan / acceptance

1. Add a small release-maintainer-only archiver `scripts/build_researcher_archive.py`, not a new TF semantic model, plugin, auto-download mechanism or runtime dependency.
2. Package **only** `tf/*.tf`, the three working `app/` files, `LICENSE_SCOPE.md`, and a self-contained `START_HERE.txt` with local unpack, `pip install 'text-fabric>=13.1,<14'`, browser launch and query instructions. No source checkout, Brown XML, `iip_tf` package, build-report JSON dependency, or diagnostic data needed to browse.
3. Before writing an archive require a successful pinned build report with 5,535 converted source files, zero failed records, a nonempty converter identity, and exact equality between the report's native feature SHA-256 inventory and the actual feature bytes. Refuse missing TF warp files, source symlinks, and occupied output paths. Normalize archive ordering/timestamps/owner metadata so two invocations with the same bytes give the same archive.
4. RED-first tests: missing packaging function, successful extraction with native TF/app/licence/instructions, deterministic bytes, malformed/incomplete reports, missing/modified TF feature, symlink input, nonempty destination protection. Run real pytest RED before implementation.
5. GREEN implementation, focused pytest and the full fast CI suite. Add no new licensing logic or encoding transformations.
6. The authenticated pinned native CI workflow must build a candidate archive **after** the existing full native/browser validation, extract into a separate location, then load `Fabric(locations=...)` and exercise section search/text and a real Flask homepage and passage request via `tf.advanced.app.findApp` + `tf.browser`. This acceptance cannot import `iip_tf` or read the source directory. Then upload a temporary CI archive, explicitly **not** a release asset.
7. Exact final-head all applicable CI gates must pass, followed by logically independent code and scholarly-adversarial review, then merge. #10 stays open until a persistent, properly attributed public corpus artifact and a clean separate-machine retrieval/load are verified. #12 stays blocked.

## Boundaries and failure policy

Do not publish this candidate as an official 0.1.0 corpus solely because the packager works. All native annotations, reading layers, bibliography and other scholarly semantics remain in the TF features; the archive has no semantic sidecar. An archive checksum or source inventory is a delivery check, not an excuse to build new general-purpose integrity infrastructure.
