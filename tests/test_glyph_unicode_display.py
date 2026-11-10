"""#58 RED-first: exact Unicode-or-source fallback policy for known empty g@ref."""

from __future__ import annotations

import unicodedata

import pytest
from iip_tf.glyph_unicode import (
    GLYPH_UNICODE_MAP,
    REVIEWED_GLYPH_REFS,
    GlyphDisplayError,
    glyph_display_token,
)

from iip_tf.tf_writer import _otext


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("phoen-gaml", "\U00010902"),
        ("phoen-delt", "\U00010903"),
        ("phoen-wau", "\U00010905"),
        ("phoen-mem", "\U0001090c"),
        ("phoen-aleph", "\U00010900"),
        ("phoen-1", "\U00010916"),
        ("phoen-10", "\U00010917"),
        ("phoen-20", "\U00010918"),
        ("phoen-100", "\U00010919"),
        ("phoen-2", "\U0001091a"),
        ("phoen-3", "\U0001091b"),
    ],
)
def test_known_source_refs_use_exact_single_unicode_scalar(ref: str, expected: str) -> None:
    assert glyph_display_token(ref) == expected
    assert len(expected) == 1
    assert unicodedata.name(expected).startswith("PHOENICIAN ")


@pytest.mark.parametrize(
    "ref",
    ["bird", "phoen-4", "phoen-6", "phoen-???", "one-vertical-stroke", "ivy leaf"],
)
def test_no_exact_scalar_remains_visible_as_source_label(ref: str) -> None:
    assert glyph_display_token(ref) == f"(({ref}))"


def test_reviewed_policy_covers_every_pinned_source_ref_without_guessing() -> None:
    assert len(REVIEWED_GLYPH_REFS) == 153
    assert len(GLYPH_UNICODE_MAP) == 16
    assert set(GLYPH_UNICODE_MAP) <= REVIEWED_GLYPH_REFS
    assert len(REVIEWED_GLYPH_REFS - set(GLYPH_UNICODE_MAP)) == 137
    assert "phoen-4" not in GLYPH_UNICODE_MAP
    assert "Palaeo-Hebrew-Yod" not in GLYPH_UNICODE_MAP


@pytest.mark.parametrize("unknown", ["phoen-new", "<img src=x>", "PHOEN-GAML", ""])
def test_unreviewed_empty_glyph_refs_fail_closed(unknown: str) -> None:
    with pytest.raises(GlyphDisplayError, match="unreviewed"):
        glyph_display_token(unknown)


def test_derived_text_formats_leave_source_and_existing_formats_unchanged() -> None:
    formats = _otext()
    assert formats["fmt:text-orig-full"] == "{primary_glyph}{primary_after}"
    assert formats["fmt:text-orig-refs-full"] == (
        "{primary_glyph}{primary_ref_token}{primary_after}"
    )
    assert formats["fmt:text-orig-unicode-full"] == (
        "{primary_glyph}{primary_unicode_ref_token}{primary_after}"
    )
    # Native browsing must retain normalized layers, including translations.
    assert "fmt:text-section-normalized-unicode-full" in formats
    normalized = formats["fmt:text-section-normalized-unicode-full"]
    assert "{transcription_unicode_ref_token}" in normalized
    assert "{translation_glyph}{translation_after}" in normalized
