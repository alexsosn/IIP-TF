"""Issue #76: native TF browser must close precisely delimited editorial spans."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from tf.browser.web import setup  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

APP = Path(__file__).resolve().parents[1] / "app"


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _tei(source: str) -> str:
    return (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Editorial scope</title>"
        "<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>"
        "</titleStmt><publicationStmt><idno>scope</idno></publicationStmt>"
        "</fileDesc></teiHeader><text><body>"
        '<div type="edition" subtype="transcription"><p>'
        f"{source}</p></div></body></text></TEI>"
    )


@pytest.fixture
def native(tmp_path: Path) -> tuple[Any, Any]:
    examples = {
        "multi": 'A<supplied reason="lost">BC</supplied>D<unclear>EF</unclear>G',
        "nested": 'A<supplied reason="lost">B<unclear>CD</unclear>E</supplied>F',
        "same": "<supplied><unclear>AB</unclear></supplied>C",
        "expansion": "A<expan><abbr>BC</abbr><ex>DE</ex></expan>F",
        "rtl": 'א<supplied reason="lost">טב</supplied>ג',
        "gap": 'A<gap reason="lost" extent="unknown" unit="character"/>B',
        "spacing": 'A<supplied reason="lost">BC</supplied> DE',
        "crossline": "A<supplied>BC<lb/>DE</supplied>F",
        "clean": "XYZ",
    }
    irs = []
    for record_id, source in examples.items():
        file = tmp_path / f"{record_id}.xml"
        file.write_text(_tei(source), encoding="utf-8")
        irs.append(parse_epidoc_file(file, source_revision="fixture-revision"))
    location = tmp_path / "native-tf"
    write_tf_corpus(tuple(irs), location, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(location), silent=True).loadAll(silent=True)
    assert api
    app: Any = setup(False, f"app:{APP}", f"--locations={location}", "-noweb")
    assert app
    return api, app


def _passage(native: tuple[Any, Any], record_id: str) -> tuple[str, str]:
    api, app = native
    owner = api.T.nodeFromSection((record_id,))
    assert owner is not None
    line = api.L.d(owner, otype="line")[0]
    section = api.T.sectionFromNode(line)
    with app.test_client() as client:
        response = client.post(
            "/passage", data={"sec0": record_id, "sec1": str(section[1])}
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert isinstance(payload["table"], str)
    visible = _Visible()
    visible.feed(payload["table"])
    return payload["table"], "".join(visible.parts)


def _reading(visible: str) -> str:
    """Remove ONLY visibly bracketed editorial note labels, never glyphs."""
    return re.sub(r"⟦[^⟧]*⟧", "", visible).strip().removeprefix("1 ").strip()


def test_open_and_close_exact_supplied_unclear_ranges(native: tuple[Any, Any]) -> None:
    api, _ = native
    owner = api.T.nodeFromSection(("multi",))
    assert owner is not None
    _, text = _passage(native, "multi")
    assert "A⟦supplied reason=lost⟧BC⟦/supplied⟧D⟦unclear⟧EF⟦/unclear⟧G" in text
    assert api.T.text(owner, fmt="text-orig-full") == "ABCDEFG"
    assert "ABCDEFG" in _reading(text)


def test_nested_scope_closes_inner_before_outer(native: tuple[Any, Any]) -> None:
    _, text = _passage(native, "nested")
    assert "A⟦supplied reason=lost⟧B⟦unclear⟧CD⟦/unclear⟧E⟦/supplied⟧F" in text
    _, same = _passage(native, "same")
    assert "⟦supplied⟧⟦unclear⟧AB⟦/unclear⟧⟦/supplied⟧C" in same


def test_abbreviation_expansion_boundaries(native: tuple[Any, Any]) -> None:
    _, text = _passage(native, "expansion")
    assert "⟦abbr⟧BC⟦/abbr⟧" in text
    assert "⟦ex⟧DE⟦/ex⟧" in text
    assert "ABCDEF" in _reading(text)


def test_rtl_scope_has_both_boundaries_without_reordering_source(
    native: tuple[Any, Any],
) -> None:
    html, text = _passage(native, "rtl")
    assert "א⟦supplied reason=lost⟧טב⟦/supplied⟧ג" in text
    assert "אטבג" in _reading(text)
    assert 'class="iip-editorial-note"' in html


def test_point_gap_is_not_falsely_rendered_as_a_span(native: tuple[Any, Any]) -> None:
    _, text = _passage(native, "gap")
    assert "A⟦gap reason=lost extent=unknown unit=character⟧B" in text
    assert "⟦/gap⟧" not in text
    assert "AB" in _reading(text)


def test_plain_record_remains_free_of_editorial_boundaries(native: tuple[Any, Any]) -> None:
    _, text = _passage(native, "clean")
    assert "XYZ" in text
    assert "⟦" not in text


def test_closing_scope_precedes_whitespace_from_source_tail(
    native: tuple[Any, Any],
) -> None:
    api, _ = native
    node = api.T.nodeFromSection(("spacing",))
    assert node is not None
    source = api.T.text(node, fmt="text-orig-full")
    assert source == "ABC DE"
    _, text = _passage(native, "spacing")
    assert "A⟦supplied reason=lost⟧BC⟦/supplied⟧ DE" in text
    assert source in _reading(text)


def test_editorial_scope_across_line_break_closes_after_last_sign(
    native: tuple[Any, Any],
) -> None:
    api, _ = native
    owner = api.T.nodeFromSection(("crossline",))
    assert owner is not None
    assert len(api.L.d(owner, otype="line")) == 2
    _, text = _passage(native, "crossline")
    assert text.count("⟦supplied⟧") == 1
    assert text.count("⟦/supplied⟧") == 1
    assert text.index("⟦/supplied⟧") > text.index("DE")
    assert text.index("⟦/supplied⟧") < text.index("F")
