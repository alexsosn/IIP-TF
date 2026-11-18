# #10 public researcher-download documentation

## Research
- Merged PR #122 at `4d171fb7425773b8500afe9dda9ee16145ddb23b` adds a one-time public `corpus-data-0.1.0rc1` prerelease workflow and anonymous fresh runner acceptance.
- Distribution guide still calls the corpus an unavailable candidate and `README.md` says there is no permanent public artifact.
- The release publication run is `https://github.com/alexsosn/IIP-TF/actions/runs/44359747428`; its build is in progress. Do not claim publicly downloaded data until its `verify_public` job passes and the Release API returns three asset names.
- The official converter version remains `0.1.0.dev0`, so published corpus data should be explicitly called a **data prerelease**, distinct from the final software 0.1.0.

## Plan and acceptance
1. RED-first tests for versioned GitHub Releases archive/checksum/provenance download links in both README and guide, plus explicit non-final status and CC BY-NC 4.0 attribution.
2. Document verified public download, `sha256sum -c` prior to extraction, and standard Text-Fabric-only installation and local browser/query path; avoid suggesting `tf alexsosn/IIP-TF` auto-downloads.
3. Update stale candidate-status wording and note public metadata includes exact Brown revision and source/converter identities; do not mislabel data as MIT.
4. Do not merge documentation until the published public URL is confirmed, independently downloaded, the SHA verified, and TF+Flask smoke green in release run #44359747428.
5. Exact-head fast CI and any triggered pinned acceptance, logically independent adversarial review, then merge. If publication fails, hold docs PR and fix the release pipeline instead.

## Skeptical checks
- Public link points to a missing or different tag/asset and is not anonymous.
- The checksum instruction references an archive path rather than the downloaded basename.
- README falsely says fully released 0.1.0, or licenses corpus text under MIT.
- Docs point to TF GitHub auto-install, which remains unsupported for this repo layout.
