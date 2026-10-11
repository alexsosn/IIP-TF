"""#54 RED: selected Aramaic word language must outrank paragraph's script code."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import IRNode, NodeType
from iip_tf.language_resolution import LanguageResolutionError, resolve_sign_languages
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _source(
    tmp_path: Path, name: str, transcription: str, segmented: str = "",
    *, main_lang: str = "arc",
) -> Path:
    path = tmp_path / f"{name}.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        f'<textLang mainLang="{main_lang}"/>'
        '</msContents></msDesc></sourceDesc></fileDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription">'
        f'<p xml:lang="heb ">{transcription}</p></div>'
        + (
            '<div type="edition" subtype="transcription_segmented"><p>'
            f'{segmented}</p></div>' if segmented else ""
        )
        + '</body></text></TEI>',
        encoding="utf-8",
    )
    return path


def _letters(ir: Any) -> list[Any]:
    return [s for s in ir.signs if s.layer.value == "transcription" and s.glyph.isalpha()]


def test_projected_arc_word_resolves_script_like_p_but_retains_exact_source(
    tmp_path: Path,
) -> None:
    source = _source(
        tmp_path, "aramaic", "אב גד",
        '<w xml:id="aramaic-w1" xml:lang="arc">אב</w> '
        '<w xml:id="aramaic-w2" xml:lang="arc">גד</w>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture")
    assert [(s.glyph, s.lang, s.lang_source, s.lang_original, s.lang_origin)
            for s in _letters(ir)] == [
        (glyph, "arc", "transcription_segmented", "heb ", "p")
        for glyph in "אבגד"
    ]
    words = ir.nodes_of_type(NodeType.WORD)
    assert len(words) == 2
    assert {word.feature("lang") for word in words} == {"arc"}
    assert {word.feature("lang_original") for word in words} == {"arc"}

    out = tmp_path / "tf"
    write_tf_corpus((ir,), out, converter_commit="unit")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    owner = api.T.nodeFromSection(("aramaic",))
    assert owner is not None
    signs = [n for n in api.L.d(owner, otype="sign") if api.F.glyph.v(n)]
    assert [api.F.lang.v(n) for n in signs] == ["arc"] * 4
    assert [api.F.lang_source.v(n) for n in signs] == ["transcription_segmented"] * 4
    assert [api.F.lang_original.v(n) for n in signs] == ["heb "] * 4
    assert [api.F.lang_origin.v(n) for n in signs] == ["p"] * 4
    assert [api.F.script.v(n) for n in signs] == ["Hebr"] * 4
    assert api.T.text(owner, fmt="text-orig-full") == "אב גד"


def test_foreign_explicit_language_unmapped_text_and_synthetic_are_not_clobbered(
    tmp_path: Path,
) -> None:
    source = _source(
        tmp_path, "mixed",
        'אב<foreign xml:lang="heb">גד</foreign>ה<lb/>ו<g ref="phoen-gaml"/>',
        '<w xml:id="mixed-w1" xml:lang="arc">אב</w>'
        '<w xml:id="mixed-w2" xml:lang="arc">גד</w>'
        '<w xml:id="mixed-w3" xml:lang="arc">ה</w>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture")
    assert [(s.glyph, s.lang, s.lang_origin) for s in _letters(ir)] == [
        ("א", "arc", "p"), ("ב", "arc", "p"),
        ("ג", "heb", "foreign"), ("ד", "heb", "foreign"),
        ("ה", "arc", "p"), ("ו", "heb", "p"),
    ]
    assert all(s.lang == "heb" for s in ir.signs if s.synthetic_kind)


def test_no_guessing_without_selected_word_or_without_hebrew_encoded_letters(
    tmp_path: Path,
) -> None:
    without_words = parse_epidoc_file(
        _source(tmp_path, "none", "אב"),
        source_revision="fixture",
    )
    latin = parse_epidoc_file(
        _source(
            tmp_path, "latin", "AB",
            '<w xml:id="latin-w1" xml:lang="arc">AB</w>',
        ),
        source_revision="fixture",
    )
    greek_record = parse_epidoc_file(
        _source(
            tmp_path, "greekrecord", "אב",
            '<w xml:id="greekrecord-w1" xml:lang="arc">אב</w>',
            main_lang="grc",
        ),
        source_revision="fixture",
    )
    for ir in (without_words, latin, greek_record):
        assert {s.lang for s in _letters(ir)} == {"heb"}
        assert {s.lang_source for s in _letters(ir)} == {"xml:lang"}


def test_cross_layer_and_explicit_foreign_aramaic_greek_are_not_affected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "foreign.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        '<textLang mainLang="arc"/></msContents></msDesc></sourceDesc>'
        '</fileDesc></teiHeader><text><body>'
        '<div type="edition" subtype="transcription"><p>'
        '<foreign xml:lang="arc-Grek">βαρ</foreign></p></div>'
        '<div type="translation"><p>English text</p></div>'
        '<div type="edition" subtype="transcription_segmented"><p>'
        '<w xml:id="foreign-w1" xml:lang="arc-Grek">βαρ</w>'
        '</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    ir = parse_epidoc_file(path, source_revision="fixture")
    assert {(s.lang, s.lang_source, s.lang_origin)
            for s in _letters(ir)} == {("arc-Grek", "xml:lang", "foreign")}
    english = [s for s in ir.signs if s.layer.value == "translation" and s.glyph]
    assert english and {s.lang for s in english} == {"eng"}


def test_drift_word_is_not_authoritative_and_conflicting_overlaps_fail_closed(
    tmp_path: Path,
) -> None:
    parsed = parse_epidoc_file(
        _source(
            tmp_path, "conflict", "אב",
            '<w xml:id="conflict-w1" xml:lang="arc">אב</w>',
        ),
        source_revision="fixture",
    )
    word = parsed.nodes_of_type(NodeType.WORD)[0]
    drift = replace(
        word, features=tuple(
            (key, "projected_with_source_drift" if key == "segmentation_status" else value)
            for key, value in word.features
        ),
    )
    baseline = replace(
        parsed,
        signs=tuple(replace(sign, lang="heb", lang_source="xml:lang") for sign in parsed.signs),
        nodes=tuple(drift if n.key == word.key else n for n in parsed.nodes),
    )
    assert {sign.lang for sign in _letters(resolve_sign_languages(baseline))} == {"heb"}

    other = IRNode(
        key="conflict#word:overlap", node_type=NodeType.WORD,
        sign_keys=word.sign_keys,
        features=(
            ("lang", "grc"),
            ("lang_source", "transcription_segmented"),
            ("segmentation_status", "projected"),
        ),
    )
    overlapped = replace(baseline, nodes=tuple(
        word if n.key == word.key else n for n in baseline.nodes
    ) + (other,))
    with pytest.raises(LanguageResolutionError, match="conflict"):
        resolve_sign_languages(overlapped)
