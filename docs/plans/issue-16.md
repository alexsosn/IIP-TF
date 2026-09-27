# Issue #16 plan — diplomatic edition audit

## Research evidence

While preparing #3 against the pinned Brown IIP source, repository search found non-empty
`div type="edition" subtype="diplomatic"` records including `egal0001.xml`,
`caes0217.xml`, `hamm0020.xml`, `hamm0027.xml`, `hamm0046.xml`,
`hamm0049.xml`, `unkn0133.xml`, and `unkn0134.xml`.

The #2 audit records the global `div@subtype=diplomatic` frequency but does not give
diplomatic descendants their own semantic context, so their inline constructs remain mixed
into `other`.

## Contract

Extend the existing deterministic audit with:

- a `diplomatic` element/attribute context;
- an `editions.by_subtype` summary for every observed `div type="edition"` subtype;
- per-subtype counts for divs, distinct records, meaningfully non-empty divs/records,
  line breaks, nested textparts, and presence of `xml:id`, `corresp`, `ana`, and
  `xml:lang`;
- a human-readable edition-layer table and diplomatic construct table;
- rare diplomatic constructs included in the schema-decision surface.

The audit remains descriptive: it must not infer alignment between diplomatic and
transcription layers.

## RED-first tests

A fixture contains:

- a non-empty diplomatic edition with `g`, `gap`, `lb`, `corresp`, `ana`,
  `xml:id`, and `xml:lang`;
- an empty diplomatic edition in another record;
- a normal transcription and segmented transcription;
- a nested diplomatic `textpart`.

The RED contract requires edition/subtype statistics and diplomatic construct reporting
before production code is changed.

## Full-source gate

The existing pinned-source workflow must regenerate the canonical JSON/Markdown and prove
the committed evidence is byte-current. No workflow write permission or self-push is
allowed.

## Done

#16 is complete when the pinned source has been re-audited, #3 can see the diplomatic
surface directly, CI/full-source checks pass, and the exact final head has independent
adversarial review.
