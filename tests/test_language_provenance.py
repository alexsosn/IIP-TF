"""#54 RED gate: literal xml:lang provenance and originating element survive TF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _xml(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / f"{name}.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        '<textLang mainLang="arc"/></msContents></msDesc></sourceDesc>'
        '</fileDesc></teiHeader><text><body>'
        f'{body}</body></text></TEI>',
        encoding="utf-8",
    )
    return path


def test_language_provenance_tracks_nearest_explicit_tag_and_source_spaces(
    tmp_path: Path,
) -> None:
    source = _xml(
        tmp_path,
        "provenance",
        '<div type="edition" subtype="transcription">'
        '<p xml:lang="heb ">אב<supplied reason="lost">גד</supplied>'
        '<foreign xml:lang="arc-Grek ">βαρ</foreign>ה</p></div>'
        '<div type="translation"><p>English words</p></div>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture-pin")
    trans = [s for s in ir.signs if s.layer.value == "transcription" and s.glyph]
    assert "".join(s.glyph for s in trans) == "אבגדβαρה"
    assert [(s.lang, s.lang_source) for s in trans] == [
        ("heb", "xml:lang"),
        ("heb", "xml:lang"),
        ("heb", "inherited"),
        ("heb", "inherited"),
        ("arc-Grek", "xml:lang"),
        ("arc-Grek", "xml:lang"),
        ("arc-Grek", "xml:lang"),
        ("heb", "xml:lang"),
    ]
    assert [(s.lang_original, s.lang_origin) for s in trans] == [
        *[("heb ", "p")] * 4,
        *[("arc-Grek ", "foreign")] * 3,
        ("heb ", "p"),
    ]
    assert {
        (node.feature("kind"), node.feature("lang_original"), node.feature("lang_origin"))
        for node in ir.nodes
        if node.node_type == NodeType.MARKUP
        and node.feature("kind") in {"supplied", "foreign"}
    } == {
        ("supplied", "heb ", "p"),
        ("foreign", "arc-Grek ", "foreign"),
    }
    english = [s for s in ir.signs if s.layer.value == "translation" and s.glyph]
    assert english and {(s.lang, s.lang_source) for s in english} == {
        ("eng", "layer:translation")
    }
    assert all(s.lang_original is None and s.lang_origin is None for s in english)

    out = tmp_path / "tf"
    write_tf_corpus((ir,), out, converter_commit="test-commit")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    owner = api.T.nodeFromSection(("provenance",))
    assert owner is not None
    slots = [
        sign for sign in api.L.d(owner, otype="sign")
        if api.F.layer.v(sign) == "transcription" and api.F.glyph.v(sign)
    ]
    assert [api.F.lang_original.v(sign) for sign in slots] == [
        *["heb "] * 4, *["arc-Grek "] * 3, "heb "
    ]
    assert [api.F.lang_origin.v(sign) for sign in slots] == [
        *["p"] * 4, *["foreign"] * 3, "p"
    ]
    assert api.T.text(owner, fmt="text-orig-full") == "אבגדβαρה"


def test_segmented_word_retains_own_attribute_source_without_changing_signs(
    tmp_path: Path,
) -> None:
    source = _xml(
        tmp_path,
        "segmented",
        '<div type="edition" subtype="transcription"><p xml:lang="heb">אב</p></div>'
        '<div type="edition" subtype="transcription_segmented"><p>'
        '<w xml:id="segmented-w1" xml:lang="arc ">אב</w>'
        '</p></div>',
    )
    ir = parse_epidoc_file(source, source_revision="fixture-pin")
    words = [n for n in ir.nodes if n.node_type == NodeType.WORD]
    assert len(words) == 1
    word = words[0]
    assert word.feature("lang") == "arc"
    assert word.feature("lang_source") == "transcription_segmented"
    assert word.feature("lang_original") == "arc "
    assert word.feature("lang_origin") == "w"
    for key in word.sign_keys:
        sign = ir.sign(key)
        assert sign.lang == "heb"
        assert (sign.lang_original, sign.lang_origin) == ("heb", "p")

    out = tmp_path / "native"
    write_tf_corpus((ir,), out, converter_commit="fixture")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    (native_word,) = tuple(api.F.otype.s("word"))
    assert api.F.lang.v(native_word) == "arc"
    assert api.F.lang_original.v(native_word) == "arc "
    assert api.F.lang_origin.v(native_word) == "w"
    assert api.T.text(api.T.nodeFromSection(("segmented",)), fmt="text-orig-full") == "אב"
