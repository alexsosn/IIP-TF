# Product goals — IIP-TF

## Users and purpose

Epigraphers and historians of Israel and Palestine should be able to obtain, search, inspect and cite Brown University's Inscriptions of Israel/Palestine EpiDoc data in source-faithful native Text-Fabric, including uncertain lettering and structured inscription metadata.

## Representative research journeys

1. Find an inscription by a stable source identifier and inspect its text part, lines, sign slots and original EpiDoc source reference.
2. Search an attested word or linguistic attribute and distinguish supplied, damaged, uncertain and alternative readings.
3. Filter by attested language, region, date or inscription classifications without normalizing unknown values into false facts.
4. Follow bibliographic citations, edition references and available facsimile metadata from a result to their evidenced targets.
5. Install a self-contained release archive and open/search it in the standard TF browser without cloning the full Brown source tree.

## Minimum usable release

Publish a lightweight, independently downloadable corpus artifact with versioned provenance, upstream attribution, clean-user installation, representative native queries, working browsing and explicit missing/uncertain features. A CI-built archive is not yet a public release. The current priority is real public distribution and independently verified download/load (issue #10), then Agora registration.

## Boundaries

IIP remains the semantic authority for the EpiDoc source. Represent research semantics as native TF nodes/features/edges, not XML/JSON payloads or required sidecars. Respect upstream data rights and avoid building a competing web application, citation database or generalized publication system.

## Autonomous-development decision rules

- Select work by the researcher journeys above, not issue count or the ease of adding tests. Prefer finishing active PRs and releases over opening new tickets.
- Before introducing a new adapter, workflow, registry, protocol, or validation layer, demonstrate that an existing mechanism cannot meet a concrete acceptance need.
- Preserve source fidelity, access controls, security, and applicable upstream rights. Do not invent inferred text or silently weaken correctness gates.
- Batch repetitive data changes and reuse parameterized tests. Keep independent adversarial review proportional to risk, and validate the actual researcher path.
- If two successive cycles do not advance a journey or remove an observed blocker, reconsider the approach. Stop when the scoped deliverable works instead of generating optional infrastructure work.
