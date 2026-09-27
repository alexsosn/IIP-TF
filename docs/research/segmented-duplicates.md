# Duplicate segmented-edition research

Issue: #20

Pinned IIP source revision:

`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`

## Upstream pipeline behavior

Brown IIP's `word-segmentation/word_segmentation.py`:

- copies the normalized `edition/transcription` into a new `edition/transcription_segmented`;
- assigns token ids and `xml:lang`;
- stamps the new div with `change="cYYYY-MM-DD"`;
- **appends** the new segmented div to the body;
- does not remove an existing segmented div.

The README explicitly warns that files can get out of sync and that the change log must be used to track edits. The `change` attribute is generated from the segmentation run date; it is not a reference to `revisionDesc`.

Therefore repeated segmentation can create multiple segmented divs. XML order or the latest `change` value is not, by itself, scholarly precedence.

## Pinned-source cases

### ashk0016

Two segmented divs:

- `c2022-03-29`: empty;
- `c2023-07-10`: seven tokens, Greek.

The record itself was initially entered in 2023, so the older empty segmented div cannot be treated as an authoritative earlier textual version. The non-empty layer is the only usable segmentation.

Policy consequence: when all but one candidate are meaningfully empty, select the sole non-empty candidate and record the suppressed empty candidates.

### suhm0001

Two non-empty segmented divs:

- `c2021-06-16`;
- `c2023-07-10`.

Token-by-token canonical comparison shows:

- same 38 token ids;
- same token kinds;
- same token text and nested editorial markup;
- same token attributes after attribute-order normalization.

The difference is only serialization/whitespace/attribute ordering plus the parent `change` value.

Brown's `2023-07-10_errors.txt` also reports duplicate token ids after the rerun.

Policy consequence: semantically equivalent reruns can be collapsed deterministically. Selection of one physical div does not alter corpus semantics, but all source `change` values remain provenance.

### zoor0453

Two non-empty segmented divs with the same 13 token ids, token kinds, text, and nested markup:

- `c2021-06-16`: every token has `xml:lang="arc"`;
- `c2022-03-29`: the same tokens have `xml:lang="grc"`.

Relevant upstream history:

- the 2021 segmented layer was introduced while the record had `textLang mainLang="arc"`;
- commit `b9c8ce6...`, explicitly titled “testing segmented file zoor0453”, changed `mainLang` from `arc` to `grc`;
- the current segmentation script derives token `xml:lang` from `textLang/@mainLang` when no foreign-language override exists;
- `20220329errors.txt` reports `ID zoor0453-1 already defined` for the rerun, proving the appended second layer produced duplicate ids and failed the downstream list-building path;
- the normalized transcription itself remains separately marked `xml:lang="heb"`, so the record contains a genuine upstream metadata inconsistency that must not be silently normalized by IIP-TF.

Policy consequence: for this exact pinned source revision, retain the pre-rerun `c2021-06-16` segmented layer as the token-source layer, record that the suppressed rerun disagrees in `xml:lang`, and expose the anomaly in provenance/diagnostics. This is a narrow source-history override, not a generic “earliest wins” rule.

## Generic resolver policy

For a record's `transcription_segmented` candidates:

1. no candidates → no segmented layer;
2. one candidate → use it;
3. multiple candidates with exactly one meaningfully non-empty candidate → use that one;
4. multiple non-empty candidates with identical canonical token semantics → collapse them as equivalent reruns and use the first source occurrence deterministically;
5. a pinned-source override may resolve a known metadata-only conflict only when the observed candidates exactly match the researched expected shape;
6. every other multiple non-empty semantic conflict fails closed.

Canonical token semantics preserve token kind, id, attributes, text, and nested editorial markup while ignoring serialization whitespace, XML attribute order, parent `change`, and inter-token whitespace.

The resolver must never concatenate duplicate segmented layers and must never silently choose the latest run.
