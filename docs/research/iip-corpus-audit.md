# IIP corpus audit

Source revision: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`

This report is generated from `iip-inventory.json`; counts are not hand-edited.

## File accounting

- Total XML files: **5536**
- Parsed: **5529**
- Malformed/unreadable: **7**
- Test/non-inscription records: **1**

### Malformed/unreadable files

- `bqut0002.xml`
- `caes0433.xml`
- `sepp0018.xml`
- `sepp0019.xml`
- `sepp0020.xml`
- `sepp0021.xml`
- `sepp0024.xml`

## Identity

- Distinct XML ids: **5519**
- Missing XML ids: **0**
- Duplicate XML ids: **9**
- Distinct IIP ids: **5488**
- Missing IIP ids: **0**
- Duplicate IIP ids: **26**

### Duplicate XML identities

- `jaff0103`: `jaff0103.xml`, `jaff0105.xml`
- `jaff0108`: `jaff0108.xml`, `jaff0109.xml`
- `jeru0365`: `jeru0364.xml`, `jeru0365.xml`
- `jeru0366`: `jeru0336.xml`, `jeru0366.xml`
- `jeru0462`: `jeru0461.xml`, `jeru0462.xml`
- `jeru0619`: `jeru0618.xml`, `jeru0619.xml`
- `mare0190`: `mare0190.xml`, `mare0191.xml`
- `odob0025`: `odob0025.xml`, `odob0026.xml`
- `sina0134`: `sina0132.xml`, `sina0134.xml`

### Duplicate IIP identities

- `Bleh 0015`: `bleh0012.xml`, `bleh0015.xml`
- `Jaff 0103`: `jaff0103.xml`, `jaff0105.xml`
- `Jaff 0108`: `jaff0108.xml`, `jaff0109.xml`
- `Jeru 0312`: `jeru0312.xml`, `jeru0313.xml`
- `Jeru 0350`: `jeru0349.xml`, `jeru0350.xml`
- `Jeru 0365`: `jeru0364.xml`, `jeru0365.xml`
- `Jeru 0366`: `jeru0336.xml`, `jeru0366.xml`
- `Jeru 0462`: `jeru0461.xml`, `jeru0462.xml`
- `Jeru 0619`: `jeru0618.xml`, `jeru0619.xml`
- `Mare 0125`: `mare0125.xml`, `mare0126.xml`
- `Mare 0234`: `mare0123.xml`, `mare0234.xml`
- `Mare0190`: `mare0190.xml`, `mare0191.xml`
- `Masa 0613`: `masa0612.xml`, `masa0613.xml`
- `Mero 0001`: `mero0001.xml`, `mero0002.xml`
- `Mger 0118`: `mger0118.xml`, `mger0119.xml`
- `Odob 0025`: `odob0025.xml`, `odob0026.xml`
- `Sina 0134`: `sina0132.xml`, `sina0134.xml`
- `beth0283`: `beth0283.xml`, `bloy0001.xml`, `shik0004.xml`
- `elus0105`: `elus0105.xml`, `elus0106.xml`
- `emma0001`: `emma0001.xml`, `emma0002.xml`
- `jeri0015`: `jeri0015.xml`, `jeri0022.xml`
- `jeri0017`: `arch0001.xml`, `arch0002.xml`, `arch0003.xml`, `arch0004.xml`, `jeri0017.xml`
- `zoor0336`: `zoor0336.xml`, `zoor0389.xml`
- `zoor0354`: `zoor0354.xml`, `zoor0390.xml`
- `zoor0357`: `zoor0357.xml`, `zoor0392.xml`
- `zoor0361`: `fein0001.xml`, `fein0002.xml`, `fein0003.xml`, `fein0004.xml`, `fein0005.xml`, `fein0006.xml`, `fein0007.xml`, `fein0008.xml`, `fein0009.xml`, `fein0010.xml`, `fein0011.xml`, `fein0012.xml`, `fein0013.xml`, `kqaz0001.xml`, `zoor0361.xml`, `zoor0393.xml`

## Text and segmentation

- Records with transcription: **5348**
- Records with segmented transcription: **5157**
- Records with transcription but no segmented transcription: **192**
- Records with segmented transcription but no source transcription: **1**
- Records whose transcription has no visible/source-bearing content: **212**
- Records using explicit textpart: **47**
- Line-break elements in source transcriptions: **13434**

## Edition layers

| Subtype | Divs | Records | Non-empty divs | Non-empty records | lb | textparts |
|---|---:|---:|---:|---:|---:|---:|
| `diplomatic` | 4158 | 4158 | 1349 | 1349 | 2534 | 52 |
| `transcription` | 5348 | 5348 | 5136 | 5136 | 13434 | 80 |
| `transcription_segmented` | 5160 | 5157 | 4898 | 4896 | 0 | 0 |

### Edition relation-bearing attributes

| Subtype | xml:id | corresp | ana | xml:lang |
|---|---:|---:|---:|---:|
| `diplomatic` | 433 | 281 | 3942 | 1850 |
| `transcription` | 1601 | 1438 | 5335 | 2713 |
| `transcription_segmented` | 0 | 0 | 0 | 0 |

## Languages

### Record-level textLang declarations

| Construct | Count |
|---|---:|
| `grc` | 3067 |
| `arc` | 1805 |
| `he` | 475 |
| `la` | 300 |
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
| `gap` | 5084 |
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

### diplomatic

| Construct | Count |
|---|---:|
| `lb` | 2484 |
| `gap` | 1656 |
| `unclear` | 659 |
| `g` | 252 |
| `hi` | 184 |
| `supplied` | 127 |
| `space` | 66 |
| `foreign` | 32 |
| `choice` | 27 |
| `num` | 27 |
| `am` | 22 |
| `orig` | 20 |
| `abbr` | 15 |
| `ex` | 12 |
| `expan` | 9 |
| `del` | 4 |
| `corr` | 2 |
| `sic` | 2 |
| `cb` | 1 |
| `surplus` | 1 |

### textpart

| Construct | Count |
|---|---:|
| `lb` | 137 |
| `orig` | 90 |
| `unclear` | 77 |
| `gap` | 69 |
| `supplied` | 46 |
| `abbr` | 43 |
| `ex` | 33 |
| `expan` | 33 |
| `ab` | 28 |
| `choice` | 26 |
| `reg` | 21 |
| `hi` | 20 |
| `g` | 19 |
| `num` | 14 |
| `space` | 13 |
| `figDesc` | 11 |
| `figure` | 11 |
| `foreign` | 6 |
| `milestone` | 4 |
| `am` | 2 |
| `del` | 1 |

## Rare schema-decision surface

The following textual/editorial constructs occur at most ten times in their context. Rarity does not make them ignorable; issue #3 must decide their native TF representation or explicitly classify them.

| Construct | Count |
|---|---:|
| `diplomatic:cb` | 1 |
| `diplomatic:surplus` | 1 |
| `textpart:del` | 1 |
| `transcription:cb` | 1 |
| `transcription:height` | 1 |
| `transcription_segmented:app` | 1 |
| `transcription_segmented:cb` | 1 |
| `transcription_segmented:height` | 1 |
| `transcription_segmented:lem` | 1 |
| `transcription_segmented:rdg` | 1 |
| `transcription_segmented:subst` | 1 |
| `diplomatic:corr` | 2 |
| `diplomatic:sic` | 2 |
| `textpart:am` | 2 |
| `transcription_segmented:milestone` | 2 |
| `transcription_segmented:add` | 3 |
| `transcription_segmented:reg` | 3 |
| `diplomatic:del` | 4 |
| `textpart:milestone` | 4 |
| `transcription:handShift` | 4 |
| `transcription:subst` | 4 |
| `textpart:foreign` | 6 |
| `transcription:add` | 6 |
| `transcription:figDesc` | 6 |
| `transcription:figure` | 6 |
| `transcription_segmented:foreign` | 7 |
| `diplomatic:expan` | 9 |

## Mapping implications for issue #3

1. Segmented and unsegmented coverage must be modelled separately; token boundaries may only be taken from source evidence.
2. Every textual/editorial construct listed above needs an explicit mapping decision. The audit does not authorize silent dropping.
3. Repeatable metadata whose observed per-record maximum exceeds one cannot be safely represented as a single scalar inscription feature without a loss rule.
4. Licence/provenance features must preserve the pinned source revision and the verified upstream attribution requirements.

