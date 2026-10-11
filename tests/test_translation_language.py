"""Issue #53 RED: English prose must not inherit inscription text language."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _fixture(tmp_path: Path, record: str, translations: str) -> Path:
    source = tmp_path / f"{record}.xml"
    source.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        '<textLang mainLang="grc"/></msContents></msDesc></sourceDesc>'
        '</fileDesc></teiHeader><text><body>'
        '<div type="edition" subtype="transcription"><p>ΜΝΗΣΘΗ</p></div>'
        f"{translations}"
        '</body></text></TEI>',
        encoding="utf-8",
    )
    return source


def _signs(ir: Any, layer: str) -> list[Any]:
    return [s for s in ir.signs if s.layer.value == layer and s.glyph]


def test_english_translation_and_commentary_are_explicit_converter_inference(
    tmp_path: Path,
) -> None:
    source = _fixture(
        tmp_path,
        "english",
        '<div type="translation"><p>English translation</p></div>'
        '<div type="commentary"><p>An English note</p></div>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    original = _signs(ir, "transcription")
    translation = _signs(ir, "translation")
    commentary = _signs(ir, "commentary")
    assert original and translation and commentary
    assert {(s.lang, s.lang_source) for s in original} == {
        ("grc", "textLang.mainLang")
    }
    assert {(s.lang, s.lang_source) for s in translation} == {
        ("eng", "layer:translation")
    }
    assert {(s.lang, s.lang_source) for s in commentary} == {
        ("eng", "layer:commentary")
    }
    assert ir.identity.main_lang == "grc"

    native = tmp_path / "native"
    write_tf_corpus((ir,), native, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(native), silent=True).loadAll(silent=True)
    assert api
    owner = api.T.nodeFromSection(("english",))
    assert owner is not None
    assert api.F.main_lang.v(owner) == "grc"
    assert api.T.text(owner, fmt="text-orig-full") == "ΜΝΗΣΘΗ"
    for layer, expected, provenance in (
        ("translation", "English translation", "layer:translation"),
        ("commentary", "An English note", "layer:commentary"),
    ):
        parts = [
            n for n in api.L.d(owner, otype="textpart")
            if api.F.layer.v(n) == layer
        ]
        assert len(parts) == 1
        assert api.T.text(parts[0], fmt="text-section-normalized-full") == expected
        slots = [
            n for n in api.L.d(parts[0], otype="sign") if api.F.glyph.v(n)
        ]
        assert slots
        assert all(
            api.F.lang.v(n) == "eng"
            and api.F.lang_source.v(n) == provenance
            for n in slots
        )


def test_explicit_translation_division_language_overrides_converter_default(
    tmp_path: Path,
) -> None:
    source = _fixture(
        tmp_path,
        "declared",
        '<div type="translation" xml:lang="la"><p>Salve</p></div>'
        '<div type="commentary" xml:lang="de"><p>Erklärung</p></div>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    for layer, lang in (("translation", "la"), ("commentary", "de")):
        signs = _signs(ir, layer)
        assert signs
        assert {(s.lang, s.lang_source) for s in signs} == {(lang, "inherited")}
    assert {(s.lang, s.lang_source) for s in _signs(ir, "transcription")} == {
        ("grc", "textLang.mainLang")
    }


def test_nested_source_language_override_respected_in_english_translation(
    tmp_path: Path,
) -> None:
    source = _fixture(
        tmp_path,
        "inline",
        '<div type="translation"><p>Hello <foreign xml:lang="grc">λόγος'
        '</foreign> again</p></div>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    translation = _signs(ir, "translation")
    assert "H" in {s.glyph for s in translation}
    assert {s.lang for s in translation if s.glyph in "λόγος"} == {"grc"}
    assert {s.lang_source for s in translation if s.glyph in "λόγος"} == {
        "xml:lang"
    }
    assert all(s.lang == "eng" for s in translation if s.glyph in "Helloagain")
