# Research — metadata source-shape exceptions for schema 0.1

Issue: #34.

Pinned Brown IIP revision: `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.

The measurements below were produced by `scripts/research_issue34.py` after #15 source preflight, across every non-test XML file.

## Support paragraphs

- records with at least one non-empty direct `support/p`: **1,512**;
- maximum non-empty direct `support/p` count per record: **2**;
- exactly four records have two: `huld0001.xml`, `huld0002.xml`, `kqaz0001.xml`, `tibr0002.xml`.

In each case the two paragraphs are distinct source statements separated by a dimensions element. They are not duplicate serialization and there is no source attribute that identifies one as the canonical scalar note.

Therefore joining them into one string or choosing first/last would lose source structure.

## Nested facsimile surfaces

Only `mgha0001.xml` contains a surface nested directly inside another surface.

- maximum surface nesting depth in the pinned corpus: **2**;
- outer surface: "Left side", graphic `mgha0001b.jpg`;
- nested child surface: "Right side", graphic `mgha0001c.pg`.

There are no deeper nested surfaces in the pinned source.

Flattening the child surface to inscription ownership would erase source hierarchy.

## Schema consequence

Schema 0.1 needs two additive corrections:

1. `support_note` becomes a repeatable native node rather than an inscription scalar;
2. `facsimile_surface` may parent another `facsimile_surface`, while top-level surfaces remain inscription children.

No textual warp, section, or source-text semantics change.
