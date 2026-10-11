# Issue #54 — native encoded-script baseline (bounded first slice)

## Research — exact pinned Brown source

Brown revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`:
- `chor0001.xml`, source Git blob `f08f433383d889b6afaaf31f93edf1f725b0a9d8`: Aramaic transcription written with Hebrew code points and a source paragraph `xml:lang="heb"`. A language filter must not confuse this writing system with Hebrew linguistic identity.
- `beth0023.xml`, blob `1bd3522dc5b6c3d0ac8f4869f8693dcabd541888`: `<foreign xml:lang="arc-Grek">βαρ</foreign>` explicitly distinguishes Aramaic language from Greek script.
- `sina0114.xml`, blob `28a159b5290d0f77e9ea37c4c7c23cd1234f0e51`: Latin-letter *transliteration* `WDD LHLMT MḤṢT`, not evidence that the ancient stone was Latin-lettered.

Currently sign slots carry source `lang` but have no independent `script`; selected segmented words have their own source `lang` and no independent `script`. No whole-corpus inventory of mixed scripts is yet authenticated, so don't change source `lang`, invent original writing systems, or claim the full #54 resolution.

## Research → RED → GREEN → tests → skeptical review

1. RED actual EpiDoc→IR→native TF: Aramaic header with Hebrew letters and `xml:lang=heb` yields **`script=Hebr`** but preserves original `lang=heb`; Greek letters with `arc-Grek` yield `script=Grek` and original language; transliterated Latin source yields `script=Latn` **only for the encoded transcription**, never a claim about the stone. Also Georgian/Armenian/Phoenician and punctuation/combining/unknown controls.
2. Add `script` only on unambiguous alphabetic Unicode signs and `word` nodes whose attested aligned sign glyphs are uniformly one Unicode script; do not assign scripts to technical zero-width glyph references, bare punctuation, mixed-script words or nonalphabetic symbols. The independent `script_source=encoded_unicode` feature explicitly records provenance. Keep source `lang` unchanged in this slice.
3. Add isolated Unicode-name to ISO 15924 mapping with documented *encoded* semantics; conservatively return no classification for unknown/symbol/mixed. Tests must reject assuming Latin transliteration proves original script. No external system/sidecars.
4. Amend ADR-0001 and schema reference with the additive, limited `script`/ `script_source` contract; full #54 still requires correcting text `lang` from segmented word and separating source container script with raw `lang_original`, plus native pinned counts. Do not close #54.
5. Exact-head Ruff/MyPy/pytest, pinned real six-file canary plus Brown 5,535-record double TF build, adversarial independent review against code and named XML. Merge only when green.
