# ruff: noqa: E501
from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode, Layer
from iip_tf.segmentation_projection import SegmentationProjectionError
from iip_tf.text_parser import parse_epidoc_file


def _write(path: Path, name: str, text: str) -> Path:
    target = path / name
    target.write_text(text, encoding="utf-8")
    return target


def _nodes(ir: InscriptionIR, node_type: str) -> list[IRNode]:
    return [node for node in ir.nodes if node.node_type.value == node_type]


def test_projects_choice_word_across_break_no_without_new_slots(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "choice.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="choice">
          <text><body>
            <div type="edition" subtype="transcription" xml:id="choice.transcription">
              <p>A <choice><sic>B</sic><corr>C</corr></choice>D<lb break="no"/>E</p>
            </div>
            <div type="edition" subtype="transcription_segmented" change="c2024-01-01">
              <p><w xml:id="choice-1" xml:lang="grc">A</w>
                 <w xml:id="choice-2" xml:lang="grc"><choice><sic>B</sic><corr>C</corr></choice>DE</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    words = _nodes(ir, "word")

    assert len(words) == 2
    second = next(node for node in words if node.feature("token_id") == "choice-2")
    assert second.feature("token_kind") == "w"
    assert second.feature("lang") == "grc"
    assert second.feature("segmentation_status") == "projected"
    assert any(ir.sign(key).synthetic_kind == "line_break" for key in second.sign_keys)

    annotation = [
        node
        for node in _nodes(ir, "markup")
        if node.feature("annotation_source") == "transcription_segmented"
    ]
    assert {node.feature("kind") for node in annotation} >= {"choice", "sic", "corr"}
    assert all(sign.layer == Layer.TRANSCRIPTION for sign in ir.signs)


def test_projects_segmented_tokens_to_diplomatic_fallback_including_cb(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "fallback.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="fallback">
          <text><body>
            <div type="edition" subtype="diplomatic" xml:id="fallback.diplomatic">
              <p>A<lb/>B <cb/> C</p>
            </div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="fallback-1" xml:lang="grc">A</w>
                 <w xml:id="fallback-2" xml:lang="grc">B</w>
                 <w xml:id="fallback-3" xml:lang="grc"><cb/></w>
                 <w xml:id="fallback-4" xml:lang="grc">C</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    assert ir.node_feature("inscription", "primary_layer") == "diplomatic"

    words = _nodes(ir, "word")
    assert len(words) == 4
    cb_word = next(node for node in words if node.feature("token_id") == "fallback-3")
    assert len(cb_word.sign_keys) == 1
    assert ir.sign(cb_word.sign_keys[0]).synthetic_kind == "column_break"


def test_duplicate_candidates_preserve_provenance_but_emit_words_once(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "dupe.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="dupe">
          <text><body>
            <div type="edition" subtype="transcription" xml:id="dupe.transcription"><p>Alpha</p></div>
            <div type="edition" subtype="transcription_segmented" change="c2024-01-01">
              <p><w xml:id="dupe-1" xml:lang="grc">Alpha</w></p>
            </div>
            <div type="edition" subtype="transcription_segmented" change="c2024-02-01">
              <p><w xml:lang="grc" xml:id="dupe-1">Alpha</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    candidates = _nodes(ir, "segmentation")
    words = _nodes(ir, "word")

    assert len(candidates) == 2
    assert [node.feature("selected") for node in candidates] == [1, 0]
    assert {node.feature("resolution_status") for node in candidates} == {
        "equivalent_duplicates"
    }
    assert len(words) == 1
    selected = next(node for node in candidates if node.feature("selected") == 1)
    assert any(
        edge.edge_type == EdgeType.TOKEN_FROM
        and edge.source == words[0].key
        and edge.target == selected.key
        for edge in ir.edges
    )


def test_no_segmented_candidate_creates_no_word_or_segmentation_nodes(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "none.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="none">
          <text><body><div type="edition" subtype="transcription"><p>Alpha beta</p></div></body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    assert _nodes(ir, "segmentation") == []
    assert _nodes(ir, "word") == []


def test_apparatus_from_segmented_candidate_becomes_annotation_markup(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "app.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="app">
          <text><body>
            <div type="edition" subtype="transcription"><p>ע<app type="alternative"><lem>נ</lem><rdg>ו</rdg></app></p></div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="app-1" xml:lang="arc">ע<app type="alternative"><lem>נ</lem><rdg>ו</rdg></app></w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    annotations = [
        node
        for node in _nodes(ir, "markup")
        if node.feature("annotation_source") == "transcription_segmented"
    ]
    assert {node.feature("kind") for node in annotations} == {
        "apparatus",
        "lemma",
        "reading",
    }
    app_node = next(node for node in annotations if node.feature("kind") == "apparatus")
    lem = next(node for node in annotations if node.feature("kind") == "lemma")
    rdg = next(node for node in annotations if node.feature("kind") == "reading")
    assert IREdge(EdgeType.PARENT, lem.key, app_node.key) in ir.edges
    assert IREdge(EdgeType.PARENT, rdg.key, app_node.key) in ir.edges


def test_ambiguous_projection_fails_closed(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "ambiguous.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="ambiguous">
          <text><body>
            <div type="edition" subtype="transcription"><p>A A</p></div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="ambiguous-1" xml:lang="grc">A</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    with pytest.raises(SegmentationProjectionError, match="ambiguous"):
        parse_epidoc_file(path, source_revision="deadbeef")
