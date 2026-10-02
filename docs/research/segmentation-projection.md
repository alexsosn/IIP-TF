# Research — segmented transcription projection

Issue: #26, child of #4.

## Frozen inputs

- schema 0.1: `transcription_segmented` is annotation/provenance, not a fifth text layer;
- #20: duplicate segmented-edition resolver;
- #24/#25: canonical textual + metadata IR;
- pinned Brown IIP revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`;
- Brown's prototype `word-segmentation/word_segmentation.py`.

## Corpus facts

Pinned source contains 5,160 segmented-edition divs in 5,157 records. Three records have two
candidates; #20 selects one and suppresses one in each case. The audited token-root surface is:

- 34,087 `w`;
- 2,721 `num`;
- 2,666 top-level/token `orig` carrying `xml:id`;
- 39,474 candidate token roots total;
- subtracting the 38-token duplicate in `suhm0001` and 13-token duplicate in
  `zoor0453` gives 39,423 selected token roots. The suppressed `ashk0016` candidate is empty.

These counts are independent expectations for full-source IR validation.

## What upstream segmentation does

The upstream prototype starts from the normalized transcription paragraph, then mutates it before
inserting token wrappers. In particular it:

- removes `lb break="no"` without a separator;
- turns ordinary `lb` into whitespace;
- removes `gap`, `handShift`, encoded `space`, and some notes/orgName material;
- drops punctuation-only token wrappers and glyph-only token wrappers;
- in some runs removes `figure`;
- splits remaining content on whitespace;
- preserves inline editorial trees inside surviving tokens;
- turns a token containing top-level `num` or non-choice `orig` into a `num`/`orig`
  token root;
- moves foreign-language information onto token `xml:lang`.

Therefore selected segmented content is not required to cover every primary slot. Missing word
coverage must remain missing rather than being reconstructed heuristically.

## Primary-layer edge cases

### masa0779

The record has no normalized transcription, but has non-empty diplomatic and segmented layers.
The segmented token sequence follows the diplomatic text, including an explicit `cb`-only token.
This validates schema 0.1's rule that projection targets the selected primary source-text layer,
not transcription unconditionally.

### caes0428 and monograms

The transcription contains `choice/orig/figure` plus normalized `reg` expansions, while the
segmented layer contains only `orig` figure tokens. Word nodes therefore legitimately cover only
the source-side monogram events; normalized `reg` slots remain without guessed word nodes.

### mgha0001

A segmented word preserves `choice/sic/corr` and spans across a source `lb break="no"`.
Projection must retain both reading branches and include the existing line-break synthetic slot
inside the resulting word span even though the line break is absent from segmented XML.

### idum0375

The selected segmented token contains the sole audited `app/lem/rdg` occurrence. These elements
must become additional markup annotations over projected primary slots with
`annotation_source=transcription_segmented`; they are not discarded and create no new slots.

## Projection atoms

Primary signs already encode the textual semantics needed for alignment:

- visible atom: `("char", glyph, reading_role)`;
- zero-width atom: `("event", synthetic_kind, reading_role)`.

Line-break events are excluded from the matching stream because upstream removes all `lb`.
They remain in the original sign order and are included in a word span when they lie between the
first and last matched atom of that word.

Segmented token trees are converted to the same atom vocabulary using schema-0.1 reading roles.
The top-level token wrapper `w` is transparent; top-level `num` and `orig` retain their
semantic role as markup/token kinds.

## Determinism

Each non-empty selected token signature must match one contiguous slice of the primary matching
atom stream. Token slices must be monotonic and non-overlapping. Material omitted by the upstream
segmentation process may occur between token slices.

The complete ordered token sequence must have exactly one valid embedding. Zero embeddings are a
projection failure. More than one embedding is an ambiguity and also a release-blocking failure.
No greedy first-match policy is acceptable.

A word anchors the full primary sign interval from its first to last matched atom, thereby
retaining intervening `lb break="no"` synthetic positions.

## Provenance

Every segmented candidate becomes a `segmentation` node, selected or suppressed, with:

- candidate index;
- source change;
- selected flag;
- #20 resolution status;
- token count;
- candidate language summary;
- researched conflict fields when present.

Candidate nodes are technically anchored and owned by the inscription. They link with
`segmentation_of` to the source edition they annotate/project onto when such an edition exists.
Words from the selected candidate link back through `token_from`.

## Word features

Word nodes preserve token kind, token id, raw token language, lossless source token text,
segmentation status, and relevant token-root attributes such as `num@value`.

No morphology, lexeme, whitespace-derived words, or repaired token language is invented.

## Inline annotations

Selected segmented inline markup is projected onto the same primary slots using the atom mapping.
It receives `annotation_source=transcription_segmented` and preserves nested `parent` edges.
Token-wrapper `w` is not markup; token-root `num`/`orig` may also have a projected markup
annotation because they carry semantic EpiDoc markup in addition to being word tokens.

## Failure policy

Release-blocking:

- unknown #20 duplicate conflict;
- selected token with no projection atoms;
- no complete projection;
- more than one complete projection;
- token ids duplicated within selected candidate;
- selected inline markup whose non-empty atom span cannot be mapped;
- unsupported segmented inline element/attribute.

No raw XML or guessed fallback is emitted.

## Full-source RED: first failure classes

The first integrated pinned-source run parsed 5,475/5,535 records and exposed 60 projection
failures. Two classes are already explained by the upstream segmentation transform and have
focused RED fixtures:

1. **Removed reading wrappers.** The segmentation prototype can leave a glyph as ordinary token
   text even when the source transcription places the same glyph under source/normalized reading
   markup. A segmented atom with reading role `both` therefore carries no claim that the source
   atom also has role `both`; it may match the same glyph/event in any primary reading role.
   An explicitly source/normalized segmented atom remains strict.
2. **Empty inline markup.** Real segmented files contain empty editorial elements such as
   `<unclear/>`, `<abbr/>`, `<supplied/>`, `<ex/>`, `<choice/>`, and `<del/>`.
   These carry source provenance but no alignment atom. They are preserved as zero-span
   annotation IR nodes rather than made into text or treated as a projection failure.

The remaining failures are kept release-blocking pending further corpus-level classification.


## Full-source closure

The whole-corpus RED/fix loop reduced the initial 60 release-blocking projection failures to
zero without introducing a first-match or whitespace-tokenization fallback.

Additional measured source behaviors:

- the upstream segmentation program always starts from the first descendant `p` of the
  normalized transcription; projection therefore uses the first primary paragraph rather than
  the complete edition;
- repeated text requires global minimum-cost monotonic projection, not greedy matching;
- `g@ref` is part of glyph identity;
- selected zero-atom token roots keep token identity on their sole zero-span segmented markup
  annotation rather than creating a fake word node;
- Unicode canonically equivalent Greek code points (for example oxia/tonos encodings) are exact
  textual identity, not editorial drift;
- seven pinned records contain segmented snapshots that predate later transcription edits.
  Their commit history documents spelling/diacritic/case changes, inserted source characters,
  or an editorial-tree rewrite after the c2021 segmentation run.

For the documented stale-snapshot cases in the audited pinned Brown revision, the projector
permits a narrowly bounded edit model: at most two character-level source-drift edits inside a
token, only after a token start has been anchored by exact/case/diacritic evidence.
Case/diacritic-equivalent substitutions cost less than generic substitutions; inserted/deleted
current-source characters cost more. Semantic events and glyph refs remain strict. The complete
token sequence must still have exactly one global minimum-cost monotonic embedding. Equal-cost
alternatives remain release-blocking.

This drift exception is revision-scoped: it is enabled only for pinned revision
`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`, whose stale snapshots were audited against source
history. For any other revision, exact/role/glyph/Unicode-canonical projection remains available,
but character substitution/insertion/deletion is disabled and a mismatch fails closed until that
revision is researched.

A word touched by this bounded edit model receives
`segmentation_status=projected_with_source_drift`. Its `word_text` remains the raw segmented
snapshot while its sign span points to the current primary source text, so the source disagreement
is visible rather than silently normalized.

### Repaired-source accounting

The original audit counts exclude the seven malformed XML files because they could not be parsed
before #15. Those seven repaired records contribute:

- **7** additional segmented-edition candidates;
- **49** additional selected token roots.

Consequently the full parser, after #15 preflight, has the following frozen invariants:

- **5,167** `segmentation` provenance nodes;
- **39,472** selected segmented token identities;
- **39,463** `word` nodes;
- **9** zero-atom token identities preserved as segmented markup rather than fake words.

Thus every selected token root has a native IR identity even when it has no projectable textual
atoms.

### Final pinned-source result

On the pinned Brown revision after #15 preflight:

- 5,536 XML files accounted;
- 1 test file skipped;
- 5,535/5,535 non-test records parsed;
- 7 repaired files consumed;
- 0 projection failures.

The anchored-start bounded matcher reduced the whole-corpus parse step from roughly 140 seconds
during the unrestricted drift experiment to roughly 61 seconds on the GitHub runner while also
narrowing the fuzzy search surface.
