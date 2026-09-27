# Issue #18 plan — primary-text fallback overlap audit

## Research question

Issue #3 must choose a deterministic primary-warp source when the normal IIP
`transcription` is missing or empty. Marginal counts do not reveal the record-level overlap
between transcription, segmented transcription, and diplomatic editions.

This issue measures that overlap only. It does not choose the fallback policy.

## Source

Pinned Brown IIP source revision:

`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`

Malformed inputs remain unclassified and are accounted separately by the existing diagnostics.

## Contract

For each parsed non-test record, classify each source-text candidate layer as:

- `absent`: no edition div of that subtype;
- `empty`: one or more edition divs exist, but none is meaningfully non-empty;
- `nonempty`: at least one edition div contains source-bearing text/editorial content.

Candidate layers:

- `transcription`
- `transcription_segmented`
- `diplomatic`

The canonical inventory adds:

- deterministic full cross-tab of the three states;
- named edge-case buckets with complete filename lists;
- multiple-div diagnostics per candidate layer;
- a compact Markdown summary derived from the same inventory.

Required edge-case buckets:

- `transcription_absent_segmented_nonempty`
- `transcription_absent_or_empty_diplomatic_nonempty`
- `transcription_empty_segmented_nonempty`
- `no_nonempty_source_text_edition`
- `multiple_transcription_divs`
- `multiple_segmented_divs`
- `multiple_diplomatic_divs`

A record may belong to more than one bucket; buckets are diagnostics, not a partition.

## RED-first TDD

Fixtures cover normal three-layer records, segmented-only text, empty transcription with
diplomatic fallback evidence, empty transcription with segmented text, no nonempty
source-text layer, multiple candidate divs, and malformed XML.

The production audit is changed only after the focused tests fail for the missing contract.

## Full-source gate

Regenerate the pinned JSON/Markdown, then restore the audit workflow to its permanent
read-only exact-head freshness check. No fallback decision is implemented here.

## Done

#18 is complete when the record-level overlap evidence is committed, deterministic,
full-source fresh, and independently reviewed. #3 may then use it to freeze the primary-warp
selection/fallback rule.
