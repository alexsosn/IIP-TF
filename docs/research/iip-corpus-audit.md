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

## Primary source-text layer overlap

| Layer-state combination | Records |
|---|---:|
| `transcription=absent|transcription_segmented=absent|diplomatic=absent` | 6 |
| `transcription=absent|transcription_segmented=absent|diplomatic=empty` | 1 |
| `transcription=absent|transcription_segmented=absent|diplomatic=nonempty` | 172 |
| `transcription=absent|transcription_segmented=nonempty|diplomatic=nonempty` | 1 |
| `transcription=empty|transcription_segmented=absent|diplomatic=nonempty` | 3 |
| `transcription=empty|transcription_segmented=empty|diplomatic=empty` | 11 |
| `transcription=empty|transcription_segmented=empty|diplomatic=nonempty` | 198 |
| `transcription=nonempty|transcription_segmented=absent|diplomatic=absent` | 3 |
| `transcription=nonempty|transcription_segmented=absent|diplomatic=empty` | 104 |
| `transcription=nonempty|transcription_segmented=absent|diplomatic=nonempty` | 82 |
| `transcription=nonempty|transcription_segmented=empty|diplomatic=absent` | 1 |
| `transcription=nonempty|transcription_segmented=empty|diplomatic=empty` | 45 |
| `transcription=nonempty|transcription_segmented=empty|diplomatic=nonempty` | 6 |
| `transcription=nonempty|transcription_segmented=nonempty|diplomatic=absent` | 1360 |
| `transcription=nonempty|transcription_segmented=nonempty|diplomatic=empty` | 2648 |
| `transcription=nonempty|transcription_segmented=nonempty|diplomatic=nonempty` | 887 |

### Fallback-relevant record sets

#### `multiple_diplomatic_divs` — 0

- None

#### `multiple_segmented_divs` — 3

- `ashk0016.xml`
- `suhm0001.xml`
- `zoor0453.xml`

#### `multiple_transcription_divs` — 0

- None

#### `no_nonempty_source_text_edition` — 18

- `bani0002.xml`
- `beth0277.xml`
- `beth0278.xml`
- `bire0002.xml`
- `caes0371.xml`
- `idum0296.xml`
- `idum0304.xml`
- `jeru0076.xml`
- `knaf0001.xml`
- `mare0058.xml`
- `masa0607.xml`
- `masa0612.xml`
- `masa0624.xml`
- `masa0659.xml`
- `masa0660.xml`
- `masa0679.xml`
- `mger0359.xml`
- `zoor0321.xml`

#### `transcription_absent_or_empty_diplomatic_nonempty` — 374

- `akko0100.xml`
- `bani0005.xml`
- `beth0073.xml`
- `beth0231.xml`
- `beth0232.xml`
- `bire0001.xml`
- `bshe0031.xml`
- `bshe0100.xml`
- `bshe0136.xml`
- `bshe0137.xml`
- `bshe0138.xml`
- `bshe0139.xml`
- `bshe0161.xml`
- `butm0002.xml`
- `caes0023.xml`
- `caes0056.xml`
- `caes0064.xml`
- `caes0069.xml`
- `caes0071.xml`
- `caes0072.xml`
- `caes0076.xml`
- `caes0077.xml`
- `caes0082.xml`
- `caes0110.xml`
- `caes0111.xml`
- `caes0115.xml`
- `caes0116.xml`
- `caes0120.xml`
- `caes0121.xml`
- `caes0162.xml`
- `caes0171.xml`
- `caes0177.xml`
- `caes0182.xml`
- `caes0186.xml`
- `caes0201.xml`
- `caes0214.xml`
- `caes0215.xml`
- `caes0217.xml`
- `caes0218.xml`
- `caes0223.xml`
- `caes0226.xml`
- `caes0235.xml`
- `caes0236.xml`
- `caes0238.xml`
- `caes0239.xml`
- `caes0243.xml`
- `caes0248.xml`
- `caes0251.xml`
- `caes0253.xml`
- `caes0254.xml`
- `caes0257.xml`
- `caes0258.xml`
- `caes0263.xml`
- `caes0269.xml`
- `caes0270.xml`
- `caes0272.xml`
- `caes0274.xml`
- `caes0275.xml`
- `caes0276.xml`
- `caes0280.xml`
- `caes0287.xml`
- `caes0290.xml`
- `caes0292.xml`
- `caes0294.xml`
- `caes0297.xml`
- `caes0300.xml`
- `caes0306.xml`
- `caes0307.xml`
- `caes0310.xml`
- `caes0316.xml`
- `caes0320.xml`
- `caes0322.xml`
- `caes0328.xml`
- `caes0340.xml`
- `caes0342.xml`
- `caes0345.xml`
- `caes0346.xml`
- `caes0347.xml`
- `caes0348.xml`
- `caes0356.xml`
- `caes0357.xml`
- `caes0358.xml`
- `caes0360.xml`
- `caes0361.xml`
- `caes0362.xml`
- `caes0365.xml`
- `caes0366.xml`
- `caes0367.xml`
- `caes0368.xml`
- `caes0369.xml`
- `caes0370.xml`
- `caes0373.xml`
- `caes0374.xml`
- `caes0383.xml`
- `caes0384.xml`
- `caes0385.xml`
- `caes0386.xml`
- `caes0387.xml`
- `caes0388.xml`
- `caes0389.xml`
- `caes0390.xml`
- `caes0391.xml`
- `caes0392.xml`
- `caes0393.xml`
- `caes0395.xml`
- `caes0396.xml`
- `caes0397.xml`
- `caes0398.xml`
- `caes0399.xml`
- `caes0400.xml`
- `caes0401.xml`
- `caes0402.xml`
- `caes0403.xml`
- `caes0404.xml`
- `caes0405.xml`
- `caes0406.xml`
- `caes0407.xml`
- `caes0408.xml`
- `caes0409.xml`
- `caes0410.xml`
- `caes0419.xml`
- `caes0430.xml`
- `caes0540.xml`
- `caes0543.xml`
- `caes0545.xml`
- `caes0546.xml`
- `caes0547.xml`
- `caes0548.xml`
- `caes0549.xml`
- `caes0551.xml`
- `caes0557a.xml`
- `caes0557b.xml`
- `caes0559.xml`
- `caes0560a.xml`
- `caes0560b.xml`
- `caes0560c.xml`
- `caes0561.xml`
- `caes0562.xml`
- `caes0563a.xml`
- `caes0564d.xml`
- `caes0565a.xml`
- `caes0565b.xml`
- `caes0565c.xml`
- `caes0565d.xml`
- `caes0565e.xml`
- `caes0565f.xml`
- `caes0565g.xml`
- `caes0565h.xml`
- `caes0565i.xml`
- `caes0566a.xml`
- `caes0566b.xml`
- `caes0566c.xml`
- `caes0666.xml`
- `caes0668.xml`
- `coas0001.xml`
- `elal0019.xml`
- `elme0001.xml`
- `elme0002.xml`
- `elus0001.xml`
- `elus0008.xml`
- `elus0011.xml`
- `elus0012.xml`
- `elus0013.xml`
- `elus0014.xml`
- `elus0019.xml`
- `elus0023.xml`
- `elus0027.xml`
- `elus0028.xml`
- `elus0031.xml`
- `elus0033.xml`
- `elus0036.xml`
- `elus0037.xml`
- `elus0045.xml`
- `elus0050.xml`
- `elus0056.xml`
- `elus0060.xml`
- `elus0063.xml`
- `elus0067.xml`
- `elus0068.xml`
- `elus0073.xml`
- `elus0074.xml`
- `elus0077.xml`
- `elus0078.xml`
- `elus0105.xml`
- `fakh0005.xml`
- `fakh0007.xml`
- `fiqg0021.xml`
- `fiqg0022.xml`
- `fiqg0023.xml`
- `fiqg0026.xml`
- `geze0100.xml`
- `hafa0002.xml`
- `hafa0003.xml`
- `haif0011.xml`
- `haif0026.xml`
- `hamm0028.xml`
- `hamm0047.xml`
- `hamm0069.xml`
- `hkur0001.xml`
- `jeru0093.xml`
- `jeru0301.xml`
- `jeru0304.xml`
- `jeru0328.xml`
- `jeru0339.xml`
- `jeru0489.xml`
- `jeru0621.xml`
- `juei0005.xml`
- `juei0006.xml`
- `kafr0008.xml`
- `kafr0009.xml`
- `kede0005.xml`
- `keni0001.xml`
- `khis0073.xml`
- `khis0084.xml`
- `khis0089.xml`
- `kkom0001.xml`
- `mare0052.xml`
- `mare0055.xml`
- `mare0057.xml`
- `mare0059.xml`
- `mare0060.xml`
- `mare0061.xml`
- `mare0062.xml`
- `mare0063.xml`
- `mare0064.xml`
- `mare0183.xml`
- `mare0191.xml`
- `mare0192.xml`
- `mare0194.xml`
- `mare0195.xml`
- `mare0197.xml`
- `mare0207.xml`
- `mare0208.xml`
- `mare0213.xml`
- `mare0219.xml`
- `mare0260.xml`
- `mare0261.xml`
- `mare0262.xml`
- `mare0263.xml`
- `mare0264.xml`
- `mare0265.xml`
- `mare0266.xml`
- `mare0267.xml`
- `mare0268.xml`
- `mare0269.xml`
- `mare0271.xml`
- `mare0272.xml`
- `mare0273.xml`
- `mare0274.xml`
- `mare0275.xml`
- `mare0276.xml`
- `mare0277.xml`
- `mare0278.xml`
- `mare0279.xml`
- `mare0280.xml`
- `mare0281.xml`
- `mare0282.xml`
- `mare0283.xml`
- `mare0284.xml`
- `mare0285.xml`
- `mare0286.xml`
- `mare0287.xml`
- `mare0288.xml`
- `mare0289.xml`
- `mare0290.xml`
- `mare0291.xml`
- `mare0292.xml`
- `mare0293.xml`
- `mare0294.xml`
- `mare0295.xml`
- `mare0296.xml`
- `mare0297.xml`
- `mare0298.xml`
- `mare0299.xml`
- `mare0300.xml`
- `mare0307.xml`
- `mare0309.xml`
- `mare0310.xml`
- `mare0311.xml`
- `mare0322.xml`
- `mare0323.xml`
- `mare0325.xml`
- `mare0326.xml`
- `mare0327.xml`
- `mare0328.xml`
- `mare0329.xml`
- `mare0330.xml`
- `mare0331.xml`
- `mare0332.xml`
- `mare0333.xml`
- `mare0334.xml`
- `mare0335.xml`
- `mare0336.xml`
- `mare0337.xml`
- `mare0338.xml`
- `mare0339.xml`
- `mare0340.xml`
- `mare0341.xml`
- `mare0342.xml`
- `mare0343.xml`
- `mare0344.xml`
- `mare0345.xml`
- `mare0346.xml`
- `mare0347.xml`
- `mare0348.xml`
- `mare0349.xml`
- `mare0350.xml`
- `mare0372.xml`
- `mare0373.xml`
- `mare0374.xml`
- `mare0375.xml`
- `mare0376.xml`
- `mare0377.xml`
- `mare0378.xml`
- `mare0379.xml`
- `mare0380.xml`
- `mare0381.xml`
- `mare0382.xml`
- `mare0383.xml`
- `mare0384.xml`
- `mare0385.xml`
- `mare0386.xml`
- `mare0387.xml`
- `mare0388.xml`
- `mare0389.xml`
- `mare0391.xml`
- `mare0392.xml`
- `mare0393.xml`
- `mare0394.xml`
- `mare0395.xml`
- `mare0396.xml`
- `mare0397.xml`
- `mare0404.xml`
- `mare0405.xml`
- `mare0406.xml`
- `mare0408.xml`
- `mare0412.xml`
- `mare0413.xml`
- `mare0414.xml`
- `mare0415.xml`
- `mare0417.xml`
- `mare0418.xml`
- `mare0419.xml`
- `mare0420.xml`
- `mare0421.xml`
- `mare0422.xml`
- `mare0423.xml`
- `mare0425.xml`
- `mare0427.xml`
- `mare0504.xml`
- `mare0505.xml`
- `mari0002.xml`
- `mari0100.xml`
- `masa0779.xml`
- `masa0940d.xml`
- `masa0943.xml`
- `masa0945.xml`
- `masa0946.xml`
- `mger0391.xml`
- `mums0002.xml`
- `nabl0007.xml`
- `narr0005.xml`
- `narr0006.xml`
- `ness0002.xml`
- `rafi0009.xml`
- `rafi0013.xml`
- `rhan0001.xml`
- `sena0008.xml`
- `sena0009.xml`
- `sepp0031.xml`
- `sina0257.xml`
- `wibt0001.xml`
- `zoor0388.xml`
- `zoor0425.xml`

#### `transcription_absent_segmented_nonempty` — 1

- `masa0779.xml`

#### `transcription_empty_segmented_nonempty` — 0

- None

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

### Edition corresp target classes

| Source subtype | Target class | Count |
|---|---|---:|
| `diplomatic` | `transcription` | 264 |
| `diplomatic` | `translation` | 274 |
| `transcription` | `diplomatic` | 261 |
| `transcription` | `translation` | 1430 |

### Corresp target classes by source context

| Source context | Target class | Count |
|---|---|---:|
| `diplomatic` | `transcription` | 264 |
| `diplomatic` | `translation` | 274 |
| `transcription` | `diplomatic` | 261 |
| `transcription` | `translation` | 1430 |
| `translation` | `diplomatic` | 282 |
| `translation` | `transcription` | 1426 |

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

