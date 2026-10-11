"""#55 RED: name-origin codes on translation persName are not text languages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import Layer, NodeType
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _xml(tmp_path: Path, name: str, *, translation: str, transcription: str = "") -> Path:
    path = tmp_path / f"{name}.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        '<textLang mainLang="grc"/></msContents></msDesc></sourceDesc>'
        '</fileDesc></teiHeader><text><body>'
        + (
            '<div type="edition" subtype="transcription"><p>'
            + transcription + '</p></div>' if transcription else ""
        )
        + '<div type="translation"><p>'
        + translation
        + '</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    return path


def _person_entities(ir: Any) -> list[Any]:
    return [
        n for n in ir.nodes_of_type(NodeType.ENTITY)
        if n.feature("entity_kind") == "person"
    ]


def test_translation_name_origin_does_not_change_english_signs_and_survives_tf(
    tmp_path: Path,
) -> None:
    src = _xml(
        tmp_path, "cleopatra",
        translation='In memory of <persName xml:lang="egy ">Cleopatra </persName>here.',
    )
    ir = parse_epidoc_file(src, source_revision="fixture")
    (name,) = _person_entities(ir)
    assert name.feature("name_lang") == "egy"
    assert name.feature("name_lang_original") == "egy "
    assert name.feature("lang") is None
    assert name.feature("lang_source") is None
    assert name.feature("lang_original") == "egy "
    assert name.feature("lang_origin") == "persName"

    name_signs = [ir.sign(key) for key in name.sign_keys]
    assert "".join(s.glyph for s in name_signs).startswith("Cleopatra")
    assert all(s.lang == "eng" for s in name_signs)
    assert all(s.lang_source == "layer:translation" for s in name_signs)
    assert all(s.lang_original is None and s.lang_origin is None for s in name_signs)

    out = tmp_path / "tf"
    write_tf_corpus((ir,), out, converter_commit="test")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    (person,) = [
        n for n in api.F.otype.s("entity") if api.F.entity_kind.v(n) == "person"
    ]
    assert api.F.name_lang.v(person) == "egy"
    assert api.F.name_lang_original.v(person) == "egy "
    assert api.F.lang.v(person) is None
    assert api.F.lang_original.v(person) == "egy "
    assert {api.F.lang.v(s) for s in api.L.d(person, otype="sign")} == {"eng"}


@pytest.mark.parametrize(
    ("source_code", "expected"),
    [
        ("x-Arabic ", "ara"),
        ("x-Nabatean ", "arc"),
        ("x-Palmyran", "arc"),
        ("x-Semitic", "other"),
        ("x-greek-hebrew", "other"),
        ("x-unknown", "unknown"),
        ("he", "heb"),
        ("heb", "heb"),
        ("la", "lat"),
        ("hbo ", "hbo"),
        ("grc ", "grc"),
        ("arc ", "arc"),
        ("xcl", "xcl"),
    ],
)
def test_source_name_codes_are_mapped_without_text_language_leakage(
    tmp_path: Path, source_code: str, expected: str,
) -> None:
    path = _xml(
        tmp_path, "codes",
        translation=f'<persName xml:lang="{source_code}">Hareth</persName>',
    )
    ir = parse_epidoc_file(path, source_revision="fixture")
    (entity,) = _person_entities(ir)
    assert entity.feature("name_lang") == expected
    assert entity.feature("name_lang_original") == source_code
    assert entity.feature("lang") is None
    assert {ir.sign(key).lang for key in entity.sign_keys} == {"eng"}


def test_translation_name_origin_does_not_suppress_real_nested_foreign_language(
    tmp_path: Path,
) -> None:
    path = _xml(
        tmp_path, "foreign",
        translation=(
            '<persName xml:lang="x-Arabic ">Abdallah '
            '<foreign xml:lang="arc">בר</foreign> Hasan</persName>'
        ),
    )
    ir = parse_epidoc_file(path, source_revision="fixture")
    (name,) = _person_entities(ir)
    assert name.feature("name_lang") == "ara"
    signs = [ir.sign(key) for key in name.sign_keys if ir.sign(key).glyph]
    assert [(s.glyph, s.lang) for s in signs if s.glyph in "בר"] == [
        ("ב", "arc"), ("ר", "arc")
    ]
    assert all(s.lang == "eng" for s in signs if s.glyph.isascii() and s.glyph.isalpha())


def test_translation_rs_and_nontranslation_person_keep_existing_text_language(
    tmp_path: Path,
) -> None:
    src = _xml(
        tmp_path, "scope",
        transcription='<persName xml:lang="grc">Ἰωσὴφ</persName>',
        translation='<rs type="family" xml:lang="arc">son</rs> '
        '<persName>Joseph</persName>',
    )
    ir = parse_epidoc_file(src, source_revision="fixture")
    names = _person_entities(ir)
    assert len(names) == 2
    trans = next(node for node in names if node.feature("layer") == "transcription")
    assert trans.feature("lang") == "grc"
    assert trans.feature("name_lang") is None
    translation = next(node for node in names if node.feature("layer") == "translation")
    assert translation.feature("name_lang") is None
    assert {ir.sign(key).lang for key in translation.sign_keys} == {"eng"}
    family = next(
        node for node in ir.nodes_of_type(NodeType.ENTITY)
        if node.feature("entity_kind") == "reference_string"
    )
    assert family.feature("lang") == "arc"
    assert all(ir.sign(key).layer == Layer.TRANSLATION for key in family.sign_keys)


def test_unknown_explicit_name_origin_fails_closed(tmp_path: Path) -> None:
    src = _xml(
        tmp_path, "unknown",
        translation='<persName xml:lang="zz-unsupported">X</persName>',
    )
    with pytest.raises(ValueError, match="unmapped|unsupported"):
        parse_epidoc_file(src, source_revision="fixture")
