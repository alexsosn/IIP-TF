# ruff: noqa: E501
from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode, Layer, NodeType
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
    assert ir.node_feature(NodeType.INSCRIPTION, "primary_layer") == "diplomatic"

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


def test_projection_identity_ignores_upstream_reading_wrapper_changes(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "roles.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="roles">
          <text><body>
            <div type="edition" subtype="transcription">
              <p><choice><orig>ὑ</orig><reg>ὁ</reg></choice>
                 <unclear>ν</unclear><supplied reason="lost">έκταρος</supplied></p>
            </div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="roles-1" xml:lang="grc">ὑ</w>
                 <w xml:id="roles-2" xml:lang="grc">
                   <supplied reason="lost">νέκταρος</supplied>
                 </w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    words = _nodes(ir, "word")

    assert [node.feature("token_id") for node in words] == ["roles-1", "roles-2"]
    first = words[0]
    assert [ir.sign(key).glyph for key in first.sign_keys] == ["ὑ"]


def test_empty_segmented_inline_markup_is_preserved_as_zero_span_annotation(
    tmp_path: Path,
) -> None:
    path = _write(
        tmp_path,
        "empty-markup.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="empty-markup">
          <text><body>
            <div type="edition" subtype="transcription"><p>AB</p></div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="empty-markup-1" xml:lang="grc">A<unclear/>B</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    annotation = next(
        node
        for node in _nodes(ir, "markup")
        if node.feature("annotation_source") == "transcription_segmented"
        and node.feature("kind") == "unclear"
    )

    assert annotation.sign_keys == ()


def test_projection_scope_is_first_primary_paragraph_from_upstream_pipeline(
    tmp_path: Path,
) -> None:
    path = _write(
        tmp_path,
        "first-paragraph.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="first-paragraph">
          <text><body>
            <div type="edition" subtype="transcription">
              <p>A</p>
              <p>A</p>
            </div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="first-paragraph-1" xml:lang="grc">A</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    word = _nodes(ir, "word")[0]
    paragraphs = [
        node
        for node in _nodes(ir, "paragraph")
        if node.feature("layer") == "transcription"
    ]

    assert len(paragraphs) == 2
    assert word.sign_keys == paragraphs[0].sign_keys
    assert word.sign_keys != paragraphs[1].sign_keys


def test_glyph_ref_disambiguates_repeated_zero_width_glyph_events(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "glyph-ref.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="glyph-ref">
          <text><body>
            <div type="edition" subtype="transcription">
              <p><g ref="one-stroke"/> <g ref="two-strokes"/></p>
            </div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="glyph-ref-1" xml:lang="arc"><g ref="two-strokes"/></w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    word = _nodes(ir, "word")[0]

    assert len(word.sign_keys) == 1
    glyph = ir.sign(word.sign_keys[0])
    assert glyph.synthetic_kind == "glyph_ref"
    assert word.feature("token_id") == "glyph-ref-1"


def test_glyph_ref_projects_across_removed_display_glyph_text(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "glyph-display.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="glyph-display">
          <text><body>
            <div type="edition" subtype="transcription">
              <p><orig><g ref="horizontal-stroke">_</g>c</orig></p>
            </div>
            <div type="edition" subtype="transcription_segmented">
              <p><orig xml:id="glyph-display-1" xml:lang="la"><g ref="horizontal-stroke"/>c</orig></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    word = _nodes(ir, "word")[0]

    assert word.feature("token_id") == "glyph-display-1"
    assert [ir.sign(key).glyph for key in word.sign_keys if ir.sign(key).glyph] == ["_", "c"]


def test_zero_atom_token_preserves_token_identity_on_zero_span_annotation(
    tmp_path: Path,
) -> None:
    path = _write(
        tmp_path,
        "zero-token.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="zero-token">
          <text><body>
            <div type="edition" subtype="transcription"><p>A<unclear/>B</p></div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="zero-token-1" xml:lang="grc">A</w>
                 <w xml:id="zero-token-2" xml:lang="grc"><unclear/></w>
                 <w xml:id="zero-token-3" xml:lang="grc">B</w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    ir = parse_epidoc_file(path, source_revision="deadbeef")
    words = _nodes(ir, "word")
    assert [node.feature("token_id") for node in words] == [
        "zero-token-1",
        "zero-token-3",
    ]

    annotation = next(
        node
        for node in _nodes(ir, "markup")
        if node.feature("annotation_source") == "transcription_segmented"
        and node.feature("token_id") == "zero-token-2"
    )
    assert annotation.sign_keys == ()
    assert annotation.feature("token_kind") == "w"
    assert annotation.feature("lang") == "grc"
    assert annotation.feature("lang_source") == "transcription_segmented"


def test_ambiguous_zero_atom_token_shape_fails_closed(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "zero-token-ambiguous.xml",
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="zero-token-ambiguous">
          <text><body>
            <div type="edition" subtype="transcription"><p>AB</p></div>
            <div type="edition" subtype="transcription_segmented">
              <p><w xml:id="zero-token-ambiguous-1" xml:lang="grc">
                <unclear/><supplied reason="lost"/>
              </w></p>
            </div>
          </body></text>
        </TEI>""",
    )

    with pytest.raises(SegmentationProjectionError, match="zero-atom token"):
        parse_epidoc_file(path, source_revision="deadbeef")
