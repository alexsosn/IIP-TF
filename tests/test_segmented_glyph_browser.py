"""RED: segmented glyph annotations must not duplicate authored browser badges."""

from __future__ import annotations

from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from tf.browser.web import setup  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import IRNode
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

APP = Path(__file__).resolve().parents[1] / "app"


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)


def _tei(content: str) -> str:
    return (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Source glyph evidence</title>"
        "<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>"
        "</titleStmt><publicationStmt><idno>source</idno></publicationStmt>"
        "</fileDesc></teiHeader><text><body>"
        '<div type="edition" subtype="transcription"><p>'
        f"{content}</p></div></body></text></TEI>"
    )


@pytest.fixture
def fixture(tmp_path: Path) -> tuple[Any, Any]:
    irs = []
    for record_id, content in (
        ("overlap", '<g ref="cross"/>'),
        ("multiple", '<g ref="one"/><g ref="two"/>'),
        ("ordinary", "ABC"),
    ):
        path = tmp_path / f"{record_id}.xml"
        path.write_text(_tei(content), encoding="utf-8")
        ir = parse_epidoc_file(path, source_revision="fixture-revision")
        if record_id == "overlap":
            source = next(
                node for node in ir.nodes
                if node.feature("kind") == "glyph"
                and node.feature("ref") == "cross"
            )
            projected = IRNode(
                key="overlap#projected-segmentation-glyph",
                node_type=source.node_type,
                sign_keys=source.sign_keys,
                features=(
                    ("kind", "glyph"),
                    ("annotation_source", "transcription_segmented"),
                    ("layer", "transcription"),
                ),
            )
            ir = replace(ir, nodes=(*ir.nodes, projected))
        irs.append(ir)

    tf_dir = tmp_path / "native"
    write_tf_corpus(tuple(irs), tf_dir, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(tf_dir), silent=True).loadAll(silent=True)
    assert api
    webapp: Any = setup(False, f"app:{APP}", f"--locations={tf_dir}", "-noweb")
    assert webapp
    return api, webapp


def _passage(fixture: tuple[Any, Any], record_id: str) -> str:
    api, webapp = fixture
    owner = api.T.nodeFromSection((record_id,))
    assert owner is not None
    line = api.L.d(owner, otype="line")[0]
    section = api.T.sectionFromNode(line)
    with webapp.test_client() as client:
        response = client.post(
            "/passage", data={"sec0": record_id, "sec1": str(section[1])}
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert isinstance(payload["table"], str)
    visible = _Visible()
    visible.feed(payload["table"])
    return "".join(visible.chunks)


def test_coanchored_segmented_glyph_keeps_one_authored_label(
    fixture: tuple[Any, Any],
) -> None:
    api, _ = fixture
    owner = api.T.nodeFromSection(("overlap",))
    assert owner is not None
    nodes = [
        n for n in api.L.d(owner, otype="markup") if api.F.kind.v(n) == "glyph"
    ]
    assert len(nodes) == 2, "both original and projected native annotations must survive"
    assert {api.F.annotation_source.v(n) for n in nodes} == {
        None, "transcription_segmented",
    }
    sign = api.L.d(owner, otype="sign")[0]
    assert all(n in api.L.u(sign, otype="markup") for n in nodes)
    visible = _passage(fixture, "overlap")
    assert visible.count("⟦glyph ref=cross⟧") == 1
    assert "⟦glyph⟧" not in visible


def test_two_independent_source_refs_get_two_labels(fixture: tuple[Any, Any]) -> None:
    visible = _passage(fixture, "multiple")
    assert visible.count("⟦glyph ref=one⟧") == 1
    assert visible.count("⟦glyph ref=two⟧") == 1


def test_regular_source_reading_is_uncluttered(fixture: tuple[Any, Any]) -> None:
    api, _ = fixture
    owner = api.T.nodeFromSection(("ordinary",))
    assert owner is not None
    assert api.T.text(owner, fmt="text-orig-full") == "ABC"
    assert "ABC" in _passage(fixture, "ordinary")
    assert "⟦glyph" not in _passage(fixture, "ordinary")
