"""#90 RED: selected Aramaic word outranks *division* script-like lang only."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.language_audit import AramaicLanguageAudit
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _epidoc(
    tmp_path: Path, name: str, *,
    transcription: str = "אב גד",
    segmented: str = (
        '<w xml:id="div-w1" xml:lang="arc">אב</w> '
        '<w xml:id="div-w2" xml:lang="arc">גד</w>'
    ),
    main_lang: str = "arc",
    origin: str = "div",
) -> Path:
    path = tmp_path / f"{name}.xml"
    attr = ' xml:lang="heb "' if origin == "div" else ""
    p_attr = ' xml:lang="heb "' if origin == "p" else ""
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><sourceDesc><msDesc><msContents>'
        f'<textLang mainLang="{main_lang}"/>'
        '</msContents></msDesc></sourceDesc></fileDesc></teiHeader>'
        '<text><body>'
        '<div type="edition" subtype="transcription"' + attr + '>'
        '<p' + p_attr + '>' + transcription + '</p></div>'
        + (
            '<div type="edition" subtype="transcription_segmented"><p>'
            + segmented + '</p></div>' if segmented else ""
        )
        + '</body></text></TEI>',
        encoding="utf-8",
    )
    return path


def _visible(ir: Any) -> list[Any]:
    return [
        s for s in ir.signs
        if s.layer.value == "transcription" and s.glyph
    ]


def test_div_explicit_heb_in_aramaic_is_corrected_only_under_clean_source_word(
    tmp_path: Path,
) -> None:
    ir = parse_epidoc_file(_epidoc(tmp_path, "div-attested"), source_revision="pinned")
    assert [(s.glyph, s.lang, s.lang_source, s.lang_original, s.lang_origin)
            for s in _visible(ir)] == [
        (glyph, "arc", "transcription_segmented", "heb ", "div")
        for glyph in "אבגד"
    ]
    audit = AramaicLanguageAudit()
    audit.ingest(ir)
    assert audit.report()["corrected_signs"] == 4
    assert audit.report()["remaining_signs"] == 0

    out = tmp_path / "tf"
    write_tf_corpus((ir,), out, converter_commit="unit")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    node = api.T.nodeFromSection(("div-attested",))
    assert node is not None
    slots = [n for n in api.L.d(node, otype="sign") if api.F.glyph.v(n)]
    assert [api.F.lang.v(n) for n in slots] == ["arc"] * 4
    assert [api.F.lang_original.v(n) for n in slots] == ["heb "] * 4
    assert [api.F.lang_origin.v(n) for n in slots] == ["div"] * 4
    assert [api.F.script.v(n) for n in slots] == ["Hebr"] * 4
    assert api.T.text(node, fmt="text-orig-full") == "אב גד"


def test_absent_word_and_explicit_non_arc_source_words_abstain(
    tmp_path: Path,
) -> None:
    cases = (
        ("unsegmented", "", "אב"),
        ("hebrew-word", '<w xml:id="he-w" xml:lang="heb">אב</w>', "אב"),
        ("untagged", '<w xml:id="un-w">אב</w>', "אב"),
    )
    for name, segmented, transcription in cases:
        ir = parse_epidoc_file(_epidoc(
            tmp_path, name, transcription=transcription, segmented=segmented,
        ), source_revision="fixture")
        assert {(s.lang, s.lang_original, s.lang_origin)
                for s in _visible(ir)} == {("heb", "heb ", "div")}


@pytest.mark.parametrize("main_lang", ["heb", "grc", "eng"])
def test_non_aramaic_record_is_never_corrected(tmp_path: Path, main_lang: str) -> None:
    ir = parse_epidoc_file(_epidoc(
        tmp_path, f"language-{main_lang}", main_lang=main_lang,
    ), source_revision="fixture")
    assert {s.lang for s in _visible(ir)} == {"heb"}


def test_div_nested_foreign_and_non_hebrew_unicode_abstain(tmp_path: Path) -> None:
    ir = parse_epidoc_file(_epidoc(
        tmp_path, "div-mixed",
        transcription='אב<foreign xml:lang="heb">גד</foreign>AB',
        segmented=(
            '<w xml:id="dm-w1" xml:lang="arc">אב</w>'
            '<w xml:id="dm-w2" xml:lang="arc">גד</w>'
            '<w xml:id="dm-w3" xml:lang="arc">AB</w>'
        ),
    ), source_revision="fixture")
    assert [(s.glyph, s.lang, s.lang_origin) for s in _visible(ir)] == [
        ("א", "arc", "div"), ("ב", "arc", "div"),
        ("ג", "heb", "foreign"), ("ד", "heb", "foreign"),
        ("A", "heb", "div"), ("B", "heb", "div"),
    ]


def test_paragraph_origin_remains_covered_without_changed_source_provenance(
    tmp_path: Path,
) -> None:
    ir = parse_epidoc_file(_epidoc(
        tmp_path, "paragraph", origin="p",
    ), source_revision="fixture")
    assert all(s.lang == "arc" and s.lang_origin == "p" for s in _visible(ir))
    words = ir.nodes_of_type(NodeType.WORD)
    assert len(words) == 2
    assert {w.feature("lang") for w in words} == {"arc"}


def test_div_technical_and_non_transcription_layer_never_mapped(
    tmp_path: Path,
) -> None:
    ir = parse_epidoc_file(_epidoc(
        tmp_path, "div-technical", transcription="אב<lb/>גד",
        segmented='<w xml:id="dt-w1" xml:lang="arc">אב</w>',
    ), source_revision="fixture")
    assert all(s.lang == "heb" for s in ir.signs if s.synthetic_kind)
    assert len([s for s in _visible(ir) if s.lang == "arc"]) == 2
