"""Conservative Unicode-encoded script evidence, not historical stone script.

Use the Unicode Character Database name of an alphabetic code point to
identify its *encoded* writing system (ISO 15924). Unknown signs, numbers,
symbols and diacritics remain unclassified. EpiDoc language metadata is
independent, may describe a different language, and is never overwritten.
"""

from __future__ import annotations

import unicodedata
from typing import Final

# Prefixes must describe Unicode character identities, not languages.
# Extend only with explicit source-backed tests. A transliteration encoded
# in Latin characters legitimately has *encoded script* Latn, but the ancient
# inscription's original writing system is not inferred from that.
_UNICODE_NAME_SCRIPTS: Final[dict[str, str]] = {
    "LATIN ": "Latn",
    "GREEK ": "Grek",
    "HEBREW ": "Hebr",
    "ARABIC ": "Arab",
    "SYRIAC ": "Syrc",
    "PHOENICIAN ": "Phnx",
    "ARMENIAN ": "Armn",
    "GEORGIAN ": "Geor",
    "COPTIC ": "Copt",
    "CYRILLIC ": "Cyrl",
    "SAMARITAN ": "Samr",
    "ETHIOPIC ": "Ethi",
    "UGARITIC ": "Ugar",
}


def encoded_script(char: str) -> str | None:
    """Get an unambiguous ISO 15924 code from one Unicode *letter*.

    The result is deliberately undefined for zero-width technical slots,
    combining marks, digits, punctuation, symbols, or unidentified scripts.
    """
    if len(char) != 1 or not char.isalpha():
        return None
    name = unicodedata.name(char, "")
    for prefix, script in _UNICODE_NAME_SCRIPTS.items():
        if name.startswith(prefix):
            return script
    return None


def uniform_encoded_script(glyphs: tuple[str, ...]) -> str | None:
    """Return a single script if every attested letter has a known same code."""
    seen: set[str] = set()
    has_letters = False
    for glyph in glyphs:
        if not glyph or not glyph.isalpha():
            continue
        has_letters = True
        script = encoded_script(glyph)
        if script is None:
            return None
        seen.add(script)
        if len(seen) > 1:
            return None
    return next(iter(seen)) if has_letters else None
