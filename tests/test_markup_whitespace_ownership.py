# ruff: noqa: E501
"""#78: native inline editorial whitespace ownership (RED before fix)."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from tf.browser.web import setup  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

APP = Path(__file__).resolve().parents[1] / "app"


def _source(tmp_path: Path, record_id: str, text: str) -> Path:
    path = tmp_path / f"{record_id}.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><titleStmt><title>Space boundary</title>'
        '<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>'
        '</titleStmt><publicationStmt><idno>source</idno></publicationStmt>'
        '</fileDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription"><p>'
        f'{text}</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    return path


CASES = {
    "inside": "A<supplied>BC </supplied>D",
    "outside": "A<supplied>BC</supplied> D",
    "inner": "A<supplied><unclear>BC </unclear></supplied>D",
    "outer": "A<supplied><unclear>BC</unclear> </supplied>D",
    "alloutside": "A<supplied><unclear>BC</unclear></supplied> D",
    "ex": "A<expan><abbr>BC </abbr><ex>X</ex></expan>D",
    "escaped": "A<supplied>B &lt;C&gt; </supplied>D",
    "linebreak": "A<supplied>B<lb/>C </supplied>D",
}


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)


@pytest.fixture
def corpus(tmp_path: Path) -> tuple[Any, Any, dict[str, Any]]:
    irs = {
        name: parse_epidoc_file(
            _source(tmp_path, name, text), source_revision="fixture-revision"
        )
        for name, text in CASES.items()
    }
    out = tmp_path / "native"
    write_tf_corpus(tuple(irs.values()), out, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    browser: Any = setup(False, f"app:{APP}", f"--locations={out}", "-noweb")
    return api, browser, irs


def _markup(api: Any, record_id: str, kind: str) -> int:
    n = api.T.nodeFromSection((record_id,))
    assert n is not None
    return int(next(
        m for m in api.L.d(n, otype="markup") if api.F.kind.v(m) == kind
    ))


def _visible(corpus: tuple[Any, Any, dict[str, Any]], record_id: str) -> str:
    api, browser, _ = corpus
    n = api.T.nodeFromSection((record_id,))
    assert n is not None
    line = api.L.d(n, otype="line")[0]
    section = api.T.sectionFromNode(line)
    with browser.test_client() as client:
        response = client.post(
            "/passage", data={"sec0": record_id, "sec1": str(section[1])}
        )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    visible = _Visible()
    visible.feed(data["table"])
    return "".join(visible.chunks)


def test_paired_source_ownership_survives_native_tf(corpus: tuple[Any, Any, dict[str, Any]]) -> None:
    api, _, irs = corpus
    for record_id in ("inside", "outside"):
        n = api.T.nodeFromSection((record_id,))
        assert n is not None
        for fmt in ("text-orig-full", "text-orig-refs-full", "text-transcription-full", "text-layer-full"):
            assert api.T.text(n, fmt=fmt) == "ABC D"
        ir = irs[record_id]
        sup = next(
            n for n in ir.nodes
            if n.node_type == NodeType.MARKUP and n.feature("kind") == "supplied"
        )
        assert len(sup.sign_keys) == 2
        assert ir.signs[2].after == " "
    feature = "source_trailing_space_inside"
    assert api.Fs(feature).v(_markup(api, "inside", "supplied")) == "yes"
    assert api.Fs(feature).v(_markup(api, "outside", "supplied")) is None


def test_end_badge_respects_inside_or_outside_space(corpus: tuple[Any, Any, dict[str, Any]]) -> None:
    inside = _visible(corpus, "inside")
    outside = _visible(corpus, "outside")
    assert "BC ⟦/supplied⟧D" in inside
    assert "BC⟦/supplied⟧ D" in outside


def test_nested_end_badges_respect_different_space_owners(
    corpus: tuple[Any, Any, dict[str, Any]],
) -> None:
    api, _, _ = corpus
    assert api.F.source_trailing_space_inside.v(_markup(api, "inner", "unclear")) == "yes"
    assert api.F.source_trailing_space_inside.v(_markup(api, "inner", "supplied")) == "yes"
    assert api.F.source_trailing_space_inside.v(_markup(api, "outer", "unclear")) is None
    assert api.F.source_trailing_space_inside.v(_markup(api, "outer", "supplied")) == "yes"
    assert "BC ⟦/unclear⟧⟦/supplied⟧D" in _visible(corpus, "inner")
    assert "BC⟦/unclear⟧ ⟦/supplied⟧D" in _visible(corpus, "outer")
    assert "BC⟦/unclear⟧⟦/supplied⟧ D" in _visible(corpus, "alloutside")


def test_abbreviation_and_linebreak_do_not_change_source_reading(
    corpus: tuple[Any, Any, dict[str, Any]],
) -> None:
    api, _, _ = corpus
    assert api.F.source_trailing_space_inside.v(_markup(api, "ex", "abbr")) == "yes"
    assert api.F.source_trailing_space_inside.v(_markup(api, "linebreak", "supplied")) == "yes"
    for record_id in ("linebreak", "ex"):
        n = api.T.nodeFromSection((record_id,))
        assert n is not None
        assert api.T.text(n, fmt="text-orig-full")


def test_escaped_source_reading_and_boundary(corpus: tuple[Any, Any, dict[str, Any]]) -> None:
    api, _, _ = corpus
    n = api.T.nodeFromSection(("escaped",))
    assert n is not None
    assert api.T.text(n, fmt="text-orig-full") == "AB <C> D"
    html_visible = _visible(corpus, "escaped")
    assert "<C>" in html_visible
    assert "⟦/supplied⟧D" in html_visible
