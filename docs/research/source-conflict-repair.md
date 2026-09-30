# Research: seven pinned IIP files with unresolved Git conflict markers

Issue: #15

Pinned Brown IIP source revision:

`0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`

Parent revision:

`8bd81ad15df6ab801cddbab30e902aacd8ca05ed`

## Upstream status

As checked on 2026-09-27, Brown's `master` still points at the pinned revision. There is no newer authoritative upstream fix to prefer.

Exactly seven `epidoc-files/*.xml` contain literal Git conflict markers and fail XML parsing:

- `bqut0002.xml`
- `caes0433.xml`
- `sepp0018.xml`
- `sepp0019.xml`
- `sepp0020.xml`
- `sepp0021.xml`
- `sepp0024.xml`

Every conflict is confined to the `facsimile` section. None crosses into diplomatic, transcription, segmented transcription, translation, commentary, bibliography, or header scholarly metadata.

## Provenance of the corruption

All seven files are well-formed in the parent commit. The final upstream commit patch does not show a scholarly text edit at these locations; it literally adds the unresolved conflict blocks.

This gives us a three-way baseline:

- **parent / Updated upstream**: the previously committed, well-formed source;
- **Stashed changes**: concurrent local facsimile edits that were not cleanly resolved;
- **pinned final revision**: both sides plus Git conflict markers, therefore invalid XML.

A repair does not need to choose between competing textual readings. It needs to restore the parent facsimile baseline and, where the stashed side adds non-conflicting metadata, preserve that additional information too.

## Per-file repair decisions

### bqut0002

Both conflict sides contain no XML content. Remove markers only.

Parent semantics preserved:
- Zev Radovan / `bqut0002.jpg`
- Chris Zeichmann / `bqut0002d.jpg`

### caes0433

Parent/Updated side has no child at the conflict point; Stashed side adds empty `<desc/>`.

Union repair keeps `<desc/>` before the existing empty `<graphic/>`. This does not invent descriptive text.

### sepp0018

Parent/Updated side:
- `<desc>Zev Radovan</desc>`
- `<graphic url="sepp0018.jpg"/>`

Stashed side:
- same main graphic;
- commented thumbnail reference.

Union repair keeps the parent credit and one copy of the main graphic, plus the stashed thumbnail comment. It must not duplicate the main graphic.

### sepp0019

Parent/Updated side contains the existing thumbnail comment; Stashed side is empty.

Repair restores the parent comment and removes markers.

### sepp0020

Parent/Updated side is empty at the conflict point; Stashed side adds a commented thumbnail reference.

Union repair preserves the existing Zev Radovan/main-image surface and adds the comment.

### sepp0021

Both sides contain only whitespace. Remove markers only.

### sepp0024

Parent/Updated side contains a thumbnail comment; Stashed side adds `<desc>Zev Radovan</desc>`.

Union repair keeps both the existing comment and the added credit.

## Policy

The converter may apply a local repair only when all of these are true:

1. the declared source revision is exactly the pinned IIP revision above;
2. the filename is one of the seven researched files;
3. the file still contains the exact researched conflict block for that filename;
4. applying the file-specific union replacement removes all conflict markers;
5. the repaired bytes parse as well-formed XML.

If any condition changes, fail closed. Do not invoke generic XML recovery.

If a future authoritative source revision is well-formed, use it unchanged. If a future revision still contains conflict markers, fail and research that revision separately; do not carry the old repair forward by filename alone.

## Provenance contract

Every repaired document must expose:

- `repair_id = iip-2024-facsimile-conflict-union-v1`;
- original filename;
- source revision;
- repaired status;
- conflict count.

This is converter provenance, not an upstream correction claim.
