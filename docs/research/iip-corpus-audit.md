# IIP corpus audit

Source revision: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`

This report is generated from `iip-inventory.json`; counts are not hand-edited.

## File accounting

- Total XML files: **5536**
- Parsed: **5529**
- Malformed/unreadable: **7**
- Test/non-inscription records: **1**

## Identity

- Distinct XML ids: **5520**
- Missing XML ids: **0**
- Duplicate XML ids: **9**
- Distinct IIP ids: **5489**
- Missing IIP ids: **0**
- Duplicate IIP ids: **26**

## Text and segmentation

- Records with transcription: **5349**
- Records with segmented transcription: **5157**
- Records with transcription but no segmented transcription: **193**
- Records whose transcription has no visible/source-bearing content: **212**
- Records using explicit textpart: **47**
- Line-break elements in source transcriptions: **13434**

## Languages

### Record-level textLang declarations

| Construct | Count |
|---|---:|
| `grc` | 3067 |
| `arc` | 1805 |
| `he` | 475 |
| `la` | 301 |
| `phn` | 24 |
| `syc` | 6 |
| `heb` | 4 |
| `xcl` | 4 |
| `Other` | 3 |
| `geo` | 2 |
| `Geo` | 1 |
| `x-unknown` | 1 |

### Token-level xml:lang declarations

| Construct | Count |
|---|---:|
| `grc` | 23770 |
| `arc` | 11057 |
| `la` | 2121 |
| `he` | 1793 |
| `heb` | 529 |
| `phn` | 71 |
| `xcl` | 43 |
| `syc` | 41 |
| `geo` | 29 |
| `lat` | 22 |
| `Other` | 6 |
| `arc-Grek` | 1 |

## Repeatable metadata maxima

- `max_bibliography_entries_per_record`: **48**
- `max_decorations_per_record`: **20**
- `max_facsimile_graphics_per_record`: **9**
- `max_facsimile_surfaces_per_record`: **8**
- `max_hand_notes_per_record`: **1**
- `max_revision_changes_per_record`: **10**

## Licence evidence

- Records containing a licence element: **3**
- Records explicitly matching CC BY-NC 4.0 markers: **3**
- Records explicitly containing the IIP DOI: **3**

These are per-record observations. A project-wide redistribution conclusion must not be inferred from a subset without separately checking authoritative project-level terms.

## Textual/editorial construct inventory

### transcription

| Construct | Count |
|---|---:|
| `lb` | 13347 |
| `supplied` | 6373 |
| `gap` | 5097 |
| `unclear` | 4875 |
| `abbr` | 4545 |
| `ex` | 4115 |
| `expan` | 4027 |
| `num` | 3347 |
| `orig` | 2708 |
| `g` | 2460 |
| `choice` | 2015 |
| `corr` | 1382 |
| `sic` | 1379 |
| `reg` | 419 |
| `hi` | 371 |
| `foreign` | 300 |
| `am` | 173 |
| `del` | 150 |
| `space` | 110 |
| `surplus` | 90 |
| `add` | 6 |
| `figDesc` | 6 |
| `figure` | 6 |
| `handShift` | 4 |
| `subst` | 4 |
| `cb` | 1 |
| `height` | 1 |

### transcription_segmented

| Construct | Count |
|---|---:|
| `w` | 34087 |
| `supplied` | 5822 |
| `unclear` | 4768 |
| `abbr` | 4229 |
| `ex` | 3804 |
| `expan` | 3732 |
| `num` | 2721 |
| `orig` | 2671 |
| `choice` | 1556 |
| `sic` | 1357 |
| `corr` | 1356 |
| `g` | 603 |
| `hi` | 340 |
| `am` | 155 |
| `del` | 115 |
| `surplus` | 79 |
| `figDesc` | 12 |
| `figure` | 12 |
| `foreign` | 7 |
| `add` | 3 |
| `reg` | 3 |
| `milestone` | 2 |
| `app` | 1 |
| `cb` | 1 |
| `height` | 1 |
| `lem` | 1 |
| `rdg` | 1 |
| `subst` | 1 |

## Rare schema-decision surface

The following textual/editorial constructs occur at most ten times in their context. Rarity does not make them ignorable; issue #3 must decide their native TF representation or explicitly classify them.

| Construct | Count |
|---|---:|
| `transcription:cb` | 1 |
| `transcription:height` | 1 |
| `transcription_segmented:app` | 1 |
| `transcription_segmented:cb` | 1 |
| `transcription_segmented:height` | 1 |
| `transcription_segmented:lem` | 1 |
| `transcription_segmented:rdg` | 1 |
| `transcription_segmented:subst` | 1 |
| `transcription_segmented:milestone` | 2 |
| `transcription_segmented:add` | 3 |
| `transcription_segmented:reg` | 3 |
| `transcription:handShift` | 4 |
| `transcription:subst` | 4 |
| `transcription:add` | 6 |
| `transcription:figDesc` | 6 |
| `transcription:figure` | 6 |
| `transcription_segmented:foreign` | 7 |

## Mapping implications for issue #3

1. Segmented and unsegmented coverage must be modelled separately; token boundaries may only be taken from source evidence.
2. Every textual/editorial construct listed above needs an explicit mapping decision. The audit does not authorize silent dropping.
3. Repeatable metadata whose observed per-record maximum exceeds one cannot be safely represented as a single scalar inscription feature without a loss rule.
4. Licence/provenance features must preserve the pinned source revision and the verified upstream attribution requirements.

