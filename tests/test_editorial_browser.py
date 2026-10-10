"""RED: source editorial apparatus must be visible in TF's actual browser."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from tf.browser.web import setup  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)


def _tei(body: str) -> str:
    return (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Editorial test</title>"
        "<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>"
        "</titleStmt><publicationStmt><idno>source</idno></publicationStmt>"
        "</fileDesc></teiHeader>"
        '<text><body><div type="edition" subtype="transcription">'
        f"<p>{body}</p></div></body></text></TEI>"
    )


@pytest.fixture
def corpus(tmp_path: Path) -> tuple[Any, Any]:
    examples = {
        "annotated": (
            "A<supplied reason='lost' cert='low'>BC</supplied>"
            "<gap reason='lost' unit='character' extent='unknown'/>"
            "D<unclear>E</unclear>"
        ),
        "clean": "XYZ",
        "glyphonly": '<g ref="phoen-gaml" type="char"/>',
        "escaped": "A &lt;researcher-input&gt; &amp; B",
    }
    source = tmp_path / "xml"
    source.mkdir()
    irs = []
    for name, text in examples.items():
        path = source / f"{name}.xml"
        path.write_text(_tei(text), encoding="utf-8")
        irs.append(parse_epidoc_file(path, source_revision="fixture-revision"))
    tf_dir = tmp_path / "native-tf"
    write_tf_corpus(tuple(irs), tf_dir, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(tf_dir), silent=True).loadAll(silent=True)
    assert api
    webapp: Any = setup(False, f"app:{APP}", f"--locations={tf_dir}", "-noweb")
    assert webapp
    return api, webapp


def _passage(corpus: tuple[Any, Any], name: str) -> tuple[str, str]:
    api, webapp = corpus
    owner = api.T.nodeFromSection((name,))
    assert owner is not None
    lines = api.L.d(owner, otype="line")
    assert lines
    section = api.T.sectionFromNode(lines[0])
    assert section[0] == name
    with webapp.test_client() as client:
        response = client.post(
            "/passage", data={"sec0": name, "sec1": str(section[1])}
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    html = payload["table"]
    assert isinstance(html, str)
    visible = _Visible()
    visible.feed(html)
    return html, "".join(visible.chunks)


def test_visible_supply_uncertainty_and_gap_preserve_plain_reading(
    corpus: tuple[Any, Any],
) -> None:
    api, _ = corpus
    owner = api.T.nodeFromSection(("annotated",))
    assert owner is not None
    assert "ABCDE" in api.T.text(owner, fmt="text-orig-full")
    markups = api.L.d(owner, otype="markup")
    assert {"supplied", "gap", "unclear"}.issubset(
        {api.F.kind.v(m) for m in markups}
    )
    assert any(
        api.F.kind.v(m) == "supplied"
        and any(m in api.L.u(slot, otype="markup") for slot in api.E.oslots.s(m))
        for m in markups
    ), "native TF markup must be reachable from its sign slots"
    _, visible = _passage(corpus, "annotated")
    assert "A" in visible and "BC" in visible and "D" in visible
    assert "supplied" in visible.lower()
    assert "low" in visible.lower()
    assert "unclear" in visible.lower()
    assert "gap" in visible.lower()
    assert "unknown" in visible.lower()


def test_glyph_reference_only_record_not_silently_empty(
    corpus: tuple[Any, Any],
) -> None:
    api, _ = corpus
    owner = api.T.nodeFromSection(("glyphonly",))
    assert owner is not None
    assert not api.T.text(owner, fmt="text-orig-full").strip()
    refs = [
        api.F.ref.v(m) for m in api.L.d(owner, otype="markup")
        if api.F.kind.v(m) == "glyph"
    ]
    assert "phoen-gaml" in refs
    _, visible = _passage(corpus, "glyphonly")
    assert "phoen-gaml" in visible
    assert "glyph" in visible.lower()


def test_clean_reading_does_not_invent_apparatus(corpus: tuple[Any, Any]) -> None:
    _, visible = _passage(corpus, "clean")
    assert "XYZ" in visible
    assert "supplied" not in visible.lower()
    assert "gap" not in visible.lower()


def test_editorial_renderer_escapes_source_characters(
    corpus: tuple[Any, Any],
) -> None:
    html, visible = _passage(corpus, "escaped")
    assert "<researcher-input>" in visible
    assert "<researcher-input>" not in html
    assert "&lt;researcher-input&gt;" in html
