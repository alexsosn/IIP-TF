# Issue #72 — authenticated real Brown EpiDoc preflight canary

## Research

Red issue #58 pinned native TF #134 failed on Brown bshe0146 despite
green fixture CI. bshe0146 has primary source g(ref=cross) and co-anchored
segmented g(no ref) with annotation_source=transcription_segmented. A
fast, representative **real source** check should detect such genuine
projection failures before the 5,535-record *twice-built* corpus stage.

Upstream: Brown-University-Library/iip-texts at pinned commit
0b7dc8358ccdfd0c9391f049da4839fbd91c26e5. GitHub API verified
the Git blob SHA1 for six authentic EpiDoc XML files:
- bshe0146.xml: 08370d675b64cfecaa7d433f825d4f1be9d2db8e
- masa0286.xml: b90768fcfa66c525b62372639a6c6536a6251355
- abil0001.xml: a2a40b1ed15a0edfa2fc647a7cc868763ca650ac
- caes0260.xml: baab6128a6d47de4cec6d5b85fc19e6ca532a2cd
- haif0003.xml: a6d3d58af33ecd03cd0b0733e83dd2255362ac75
- chor0001.xml: f08f433383d889b6afaaf31f93edf1f725b0a9d8

Pin by **commit + expected Git blob hash**, not a mutable public branch.
Do not commit any upstream corpus XML in this converter repository.
Only fetch these six small files with short timeouts and byte limits, in
a temporary directory; the full source Git TREE authentication remains
in the independent full pinned release gate and cannot be replaced.

## TDD / implementation / review gates

1. RED offline tests for strict fixed manifest, SHA1 Git blob
   integrity, duplicate/bad/path-traversal rejection, failed download
   rejection, and real EpiDoc→native TF source-specific acceptance.
   Workflow-level RED: pinned expensive build must depend on a canary
   preflight *before* Brown archive download.
2. GREEN add scripts/validate_pinned_canary.py: fetch exactly six raw
   files from pinned revision; validate Git blob hashes, parse through
   the actual release parser (including source_repair and segmentation),
   write native TF in tempfile and verify source identities, source
   glyph-reference preservation (esp bshe0146, masa0286),
   editorial gap/expan, ordinary inscription content, and section/layer
   selection (haif0003).
3. Integrate after Ruff/MyPy/pytest in existing preflight; on failure
   fail the preflight and ensure downstream required validate job
   fails closed without starting full corpus fetch. Update PR/push
   paths to cover new script and manifest. Preserve original full
   pinned source authentication, two-build sha comparisons, reports,
   browser and always-upload-on-failure logic unchanged.
4. Exact-head CI and (real new preflight+full pinned release) pass.
   Independently inspect source and CI code to rule out silently
   skipping the full build or accepting unverified bytes. Benchmarks,
   network timeout failure mode and fallback behavior documented.
5. Independent skeptical review of exact tested head before merge.
