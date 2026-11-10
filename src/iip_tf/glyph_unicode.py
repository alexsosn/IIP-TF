"""Source-reviewed, strictly additive rendering of IIP empty glyph references.

Authenticated Brown pin: 0b7dc8358ccdfd0c9391f049da4839fbd91c26e5,
epidoc-files Git tree 4445c4878873227c73ead5e8b94f9e3487c28c3b.
153 XML-decoded source ref values from the complete #108 census.
Unicode basis: Unicode Standard 17.0, Phoenician Names List (U+10900..1091F).
These scalar identities are display approximations, never facsimile shapes
or attested glyph characters. The original TF glyph and EpiDoc ref are intact.
"""

from __future__ import annotations

from html import escape
from typing import Final


class GlyphDisplayError(ValueError):
    """Unreviewed source ref cannot silently acquire invented display."""


# Exactly one standard Unicode scalar per individually reviewed IIP ref.
# Unicode Names List: https://www.unicode.org/charts/PDF/U10900.pdf
GLYPH_UNICODE_MAP: Final[dict[str, str]] = {
    "phoen-1": "𐤖",  # U+10916 PHOENICIAN NUMBER ONE
    "phoen-10": "𐤗",  # U+10917 PHOENICIAN NUMBER TEN
    "phoen-100": "𐤙",  # U+10919 PHOENICIAN NUMBER ONE HUNDRED
    "phoen-2": "𐤚",  # U+1091A PHOENICIAN NUMBER TWO
    "phoen-20": "𐤘",  # U+10918 PHOENICIAN NUMBER TWENTY
    "phoen-3": "𐤛",  # U+1091B PHOENICIAN NUMBER THREE
    "phoen-aleph": "𐤀",  # U+10900 PHOENICIAN LETTER ALF
    "phoen-bet": "𐤁",  # U+10901 PHOENICIAN LETTER BET
    "phoen-delt": "𐤃",  # U+10903 PHOENICIAN LETTER DELT
    "phoen-gaml": "𐤂",  # U+10902 PHOENICIAN LETTER GAML
    "phoen-he": "𐤄",  # U+10904 PHOENICIAN LETTER HE
    "phoen-mem": "𐤌",  # U+1090C PHOENICIAN LETTER MEM
    "phoen-nun": "𐤍",  # U+1090D PHOENICIAN LETTER NUN
    "phoen-semk": "𐤎",  # U+1090E PHOENICIAN LETTER SEMK
    "phoen-wau": "𐤅",  # U+10905 PHOENICIAN LETTER WAU
    "phoen-yod": "𐤉",  # U+10909 PHOENICIAN LETTER YOD
}

# The complete explicit source-label fallback set. These are not guessed
# numerals or iconographic Unicode equivalents. Deliberately includes
# phoen-4, phoen-6, phoen-???, all stroke counts and symbol descriptions.
FALLBACK_GLYPH_REFS: Final[frozenset[str]] = frozenset({
    "+",
    "7-shaped-symbol",
    "HORIZONTAL-STROKE",
    "Inverted-Beta",
    "L",
    "Palaeo-Hebrew-Yod",
    "UNRECOGNIZABLE-SMEARED-MARKS",
    "archaic-aleph",
    "arrow",
    "bird",
    "black club suit",
    "candelabrum",
    "chi-rho",
    "christogram",
    "circled-cross",
    "cornucopia",
    "cross",
    "cross-rho",
    "cross-within-a-wreath",
    "curved-numeral",
    "decoration",
    "design",
    "diagonal-stroke",
    "dividing-line",
    "doodle",
    "dove",
    "downward_triangle",
    "eight-slanted-strokes",
    "eight-vertical-strokes",
    "eighteen-vertical-strokes",
    "eleven-vertical-strokes",
    "fifteen-vertical-strokes",
    "fish",
    "five-pointed-star",
    "five-right-slanted-strokes",
    "five-right-slanted-strokes-with-two-left-slanted-strokes-below-the-line",
    "five-slanted-strokes",
    "five-vertical-strokes",
    "flower-with-leaves",
    "forty-three-vertical-strokes",
    "four-slanted-strokes",
    "four-vertical-numbers",
    "four-vertical-strokes",
    "fourteen-vertical-strokes",
    "halo",
    "hedera",
    "heraldic-angular-motifs",
    "hooked-triangle",
    "horizonal-mark",
    "horizontal-line",
    "horizontal-stroke",
    "horizontal-stroke-below-the-line",
    "ivy leaf",
    "ivy-leaf",
    "leaf",
    "leaves",
    "linear-cross",
    "looped_aleph",
    "lulav",
    "menorah",
    "nine-slanted-strokes",
    "nine-vertical-strokes",
    "numeral",
    "numeral-glyph",
    "numeral-one",
    "one-angular-motif",
    "one-left-slanted-stroke",
    "one-left-slanted-stroke-and-three-right-slanted-strokes",
    "one-left-slanted-stroke-with-three-intersecting-right-strokes",
    "one-right-slanted-stroke",
    "one-slanted-stroke",
    "one-vertical-stroke",
    "pair-of-birds",
    "palm",
    "palm-branch",
    "palm-branches",
    "palm-leaf",
    "palm_branch",
    "peacock",
    "phoen-4",
    "phoen-6",
    "phoen-???",
    "pinecone",
    "reversed-beta",
    "sealing-sign",
    "seven-shaped-mark",
    "seven-slanted-strokes",
    "seven-vertical-strokes",
    "seventeen-vertical-strokes",
    "six-slanted-strokes",
    "six-vertical-strokes",
    "sixteen-plus-two-vertical-strokes",
    "sixteen-vertical-strokes",
    "sprig",
    "star",
    "star-in-a-circle",
    "staurogram",
    "sun-disc",
    "sun-disc-with-inscribed-cross",
    "symbol",
    "ten-vertical-strokes",
    "thirteen-vertical-strokes",
    "three-angular-motifs",
    "three-marks",
    "three-plus-one-vertical-strokes",
    "three-right-slanted-strokes",
    "three-right-slanted-strokes-and-two-left-slanted-strokes",
    "three-right-slanted-strokes-with-one-left-slanted-stroke-belowe-the-line",
    "three-slanted-strokes",
    "three-vertical-strokes",
    "triskele",
    "twelve-vertical-strokes",
    "twenty-five-vertical-strokes",
    "twenty-four-vertical-strokes",
    "twenty-nine-vertical-stroke",
    "twenty-one-vertical-strokes",
    "twenty-seven-vertical-strokes",
    "twenty-six-vertical-stroke",
    "twenty-two-vertical-strokes",
    "twenty-vertical-strokes",
    "twisted-stroke",
    "two-bars-forming-an-angle",
    "two-right-slanted-strokes",
    "two-right-slanted-strokes-with-one-left-slanted-stroke-below-the-line",
    "two-slanted-strokes",
    "two-vertical-strokes",
    "unknown",
    "upright-mark",
    "upside-down-menorah",
    "vertical-stroke",
    "vertical-strokes",
    "vine",
    "wedge",
    "wreath-with-an-inscribed-cross",
    "z",
    "zig-zag",
    "Κ-within-L",
})

REVIEWED_GLYPH_REFS: Final[frozenset[str]] = (
    frozenset(GLYPH_UNICODE_MAP) | FALLBACK_GLYPH_REFS
)


def glyph_display_token(ref: str) -> str:
    """Unicode for reviewed exact identities; source-faithful ((ref)) otherwise.

    Ref is the XML-decoded source value, never a fabricated source glyph.
    An unreviewed empty ref is a hard error, not an omitted character.
    """
    character = GLYPH_UNICODE_MAP.get(ref)
    if character is not None:
        return character
    if ref in FALLBACK_GLYPH_REFS:
        return f"(({escape(ref, quote=True)}))"
    raise GlyphDisplayError(f"unreviewed source glyph reference: {ref!r}")
