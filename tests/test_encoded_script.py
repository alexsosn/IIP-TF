"""RED #54: encoded writing system is separate from source language."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from iip_tf.encoded_script import encoded_script
from iip_tf.ir import IRNode, NodeType
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus
from tf.fabric import Fabric  # type: ignore[import-untyped]


def _source(
    tmp_path: Path, inscription_id: str, text: str, main_lang: str
) -> Path:
    path = tmp_path / f"{inscription_id}.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><sourceDesc><msDesc><msContents>"
        f'<textLang mainLang="{main_lang}"/>'
        "</msContents></msDesc></sourceDesc></fileDesc></teiHeader>"
        f'<text><body><div type="edition" subtype="transcription"><p>{text}</p>'
        "</div></body></text></TEI>",
        encoding="utf-8",
    )
    return path


def test_unicode_encoded_script_is_conservative_and_iso15924() -> None:
    assert encoded_script("א") == "Hebr"
    assert encoded_script("β") == "Grek"
    assert encoded_script("Ḥ") == "Latn"
    assert encoded_script("𐤀") == "Phnx"
    assert encoded_script("Ⴀ") == "Geor"
    assert encoded_script("Ա") == "Armn"
    assert encoded_script("ܐ") == "Syrc"
    assert encoded_script("ب") == "Arab"
    assert encoded_script("ᚠ") is None  # no guessed rule for unsupported script
    assert encoded_script("3") is None
    assert encoded_script(" ") is None
    assert encoded_script("ְ") is None
    assert encoded_script("") is None


def test_native_sign_script_does_not_relabel_source_language(tmp_path: Path) -> None:
    examples = (
        ("aramaic", '<p xml:lang="heb">אב</p>', "arc"),
        ("greek", '<foreign xml:lang="arc-Grek">βαρ</foreign>', "grc"),
        ("translit", "WDD LHLMT MḤṢT", "arc"),
    )
    irs = []
    for inscription_id, text, main_lang in examples:
        # p XML cannot nest under p; use a nested foreign for Aramaic.
        fragment = (
            '<foreign xml:lang="heb">אב</foreign>'
            if inscription_id == "aramaic" else text
        )
        irs.append(parse_epidoc_file(
            _source(tmp_path, inscription_id, fragment, main_lang),
            source_revision="pinned-test",
        ))
    out = tmp_path / "native"
    write_tf_corpus(tuple(irs), out, converter_commit="unit-head")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    for inscription_id, original, script in (
        ("aramaic", "heb", "Hebr"),
        ("greek", "arc-Grek", "Grek"),
        ("translit", "arc", "Latn"),
    ):
        insc = api.T.nodeFromSection((inscription_id,))
        assert insc is not None
        letters = [
            n for n in api.L.d(insc, otype="sign")
            if api.F.glyph.v(n) and api.F.glyph.v(n).isalpha()
        ]
        assert letters
        assert all(api.F.script.v(n) == script for n in letters)
        assert all(api.F.script_source.v(n) == "encoded_unicode" for n in letters)
        if inscription_id == "aramaic":
            assert all(api.F.lang.v(n) == original for n in letters)
        if inscription_id == "greek":
            assert api.F.lang.v(letters[0]) == original

    translit = api.T.nodeFromSection(("translit",))
    assert translit is not None
    assert api.T.text(translit, fmt="text-orig-full") == "WDD LHLMT MḤṢT"


def test_word_script_only_when_all_attested_letters_agree(tmp_path: Path) -> None:
    parsed = parse_epidoc_file(
        _source(tmp_path, "words", "אבβ", "arc"),
        source_revision="fixture",
    )
    letters = [sign for sign in parsed.signs if sign.glyph and sign.glyph.isalpha()]
    assert len(letters) == 3
    words = (
        IRNode(
            key="words#hebrewword", node_type=NodeType.WORD,
            sign_keys=tuple(sign.key for sign in letters[:2]),
            features=(("word_text", "אב"),),
        ),
        IRNode(
            key="words#mixedword", node_type=NodeType.WORD,
            sign_keys=tuple(sign.key for sign in letters),
            features=(("word_text", "אבβ"),),
        ),
    )
    corpus = replace(parsed, nodes=(*parsed.nodes, *words))
    output = tmp_path / "native"
    write_tf_corpus((corpus,), output, converter_commit="fixture")
    api: Any = Fabric(locations=str(output), silent=True).loadAll(silent=True)
    assert api
    hebrew = next(n for n in api.F.otype.s("word") if api.F.word_text.v(n) == "אב")
    mixed = next(n for n in api.F.otype.s("word") if api.F.word_text.v(n) == "אבβ")
    assert api.F.script.v(hebrew) == "Hebr"
    assert api.F.script_source.v(hebrew) == "encoded_unicode"
    assert api.F.script.v(mixed) is None


def test_technical_point_and_punctuation_have_no_script(tmp_path: Path) -> None:
    ir = parse_epidoc_file(
        _source(tmp_path, "glyphref", 'א<g ref="phoen-gaml"/>!', "arc"),
        source_revision="fixture",
    )
    tf = tmp_path / "native"
    write_tf_corpus((ir,), tf, converter_commit="fixture")
    api: Any = Fabric(locations=str(tf), silent=True).loadAll(silent=True)
    assert api
    insc = api.T.nodeFromSection(("glyphref",))
    assert insc is not None
    signs = api.L.d(insc, otype="sign")
    assert [api.F.script.v(s) for s in signs] == ["Hebr", None, None]
    assert api.T.text(insc, fmt="text-orig-full") == "א!"
