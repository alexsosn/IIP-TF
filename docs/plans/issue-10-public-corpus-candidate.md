# Issue #10: Publish a verified public prerelease corpus archive

## Research (2026-11-18)
- Main commit at start: `d09e6ee659ea2552e0a094c21509b139531f13d7`. No existing public GitHub Release (`GET /repos/alexsosn/IIP-TF/releases => []`).
- PR #121's exact-head CI proved a complete source-free, deterministic archive with 5,535 inscription records and an isolated TF/browser extraction smoke. That CI artifact expires after seven days.
- Existing `validate_pinned_tf.py`, `build_researcher_archive.py`, `smoke_researcher_archive.py`, and `validate_pinned_app.py` can be reused as-is; no new converter path is needed.
- Issue #10 was incorrectly closed before a public artifact existed, and was reopened. #12 is the official release gate. The data prerelease must not be confused with IIP-TF 0.1.0.
- GitHub connector cannot create Releases or upload release assets directly; a scoped GitHub Actions workflow can, with `contents:write` limited to the publishing job.

## Plan
1. Add failing tests for a publication workflow: main-only first-push/explicit manual dispatch, no PR/untrusted workflow trigger, authenticated pinned build and exact converter SHA, separate write-permission publish job, immutable prerelease tag, SHA256 file, and unauthenticated public URL download with a fresh TF-only smoke job.
2. Add a single GitHub Actions workflow that runs on its own first merge to main (and explicit manual dispatch later); does not run on every main commit.
3. Generate native corpus twice through the authenticated full-source validator; test app; create source-free archive; compute checksum; exercise extracted archive in isolated venv. Upload audited archive/checksum as temporary artifacts.
4. The distinct publication job downloads those artifacts and creates one public **prerelease** under fixed tag `corpus-data-0.1.0rc1` at the exact triggering main SHA, refusing tag reuse or replacement. Permissions for write are scoped to this job.
5. An independent verification job must download asset and SHA256 **without a GitHub token**, verify digest, extract on another runner, install Text-Fabric alone and run real queries + Flask browser smoke. If that fails, treat the prerelease as unaccepted and keep #10 open.
6. Complete exact-head normal CI, pinned native CI and adversarial review before merge. Afterwards check public release and actual verify job. Only then change researcher docs/issue status.

## Review attack cases
- Untrusted pull_request/workflow_run accidentally gains `contents:write`.
- `gh release create` uses a mutable branch or preexisting tag and silently points to old data.
- A successful upload is mistaken for successful unauthenticated download.
- Checksum file refers to a build path rather than the downloaded basename.
- Converter metadata silently changes source revision or record count.
- Released archive contains checkout paths, source XML or is unreadable by Text-Fabric because tar mtimes were zero.
- CI green on the PR does not mean the release-publishing push was executed.

## Explicit exclusions
- No automatic final `0.1.0` release, PyPI wheel, registered Agora installation, migration of corpus semantics or novel data conversion layer.
- Do not mark issue #10 completed until the external public URL has been tested.
