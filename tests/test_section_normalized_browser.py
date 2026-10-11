"""Issue #51: nonprimary textparts readable without mixing choice branches."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from tf.browser.web import setup  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

APP = Path(__file__).resolve().parents[1] / "app"


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fragments: list[str] = []

    def handle_data(self, data: str) -> None:
        self.fragments.append(data)


@pytest.fixture
def native(tmp_path: Path) -> tuple[Any, Any]:
    document = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Multi-layer reading</title>"
        "<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>"
        "</titleStmt><publicationStmt><idno>source</idno></publicationStmt>"
        "</fileDesc></teiHeader><text><body>"
        '<div type="edition" subtype="transcription"><p>'
        'A<choice><orig>X</orig><reg>Y</reg></choice>B</p></div>'
        '<div type="edition" subtype="diplomatic"><p>ΜΝΗΣΘΗ</p></div>'
        '<div type="translation"><p>Translated</p></div>'
        "</body></text></TEI>"
    )
    path = tmp_path / "multi.xml"
    path.write_text(document, encoding="utf-8")
    ir = parse_epidoc_file(path, source_revision="fixture-revision")
    tf_dir = tmp_path / "tf"
    write_tf_corpus((ir,), tf_dir, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(tf_dir), silent=True).loadAll(silent=True)
    assert api
    app: Any = setup(False, f"app:{APP}", f"--locations={tf_dir}", "-noweb")
    assert app
    return api, app


def _textpart(api: Any, layer: str) -> int:
    inscription = api.T.nodeFromSection(("multi",))
    assert inscription is not None
    matching = [
        node for node in api.L.d(inscription, otype="textpart")
        if api.F.layer.v(node) == layer
    ]
    assert len(matching) == 1
    return matching[0]


def _browse(native: tuple[Any, Any], layer: str) -> str:
    api, webapp = native
    part = _textpart(api, layer)
    line = api.L.d(part, otype="line")[0]
    section = api.T.sectionFromNode(line)
    with webapp.test_client() as client:
        response = client.post(
            "/passage", data={"sec0": "multi", "sec1": str(section[1])}
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert isinstance(payload["table"], str)
    text = _Text()
    text.feed(payload["table"])
    return "".join(text.fragments)


def test_explicit_normalized_per_layer_text_format_avoids_duplicated_variants(
    native: tuple[Any, Any],
) -> None:
    api, _ = native
    assert api.T.defaultFormat == "text-orig-full"
    expected = {
        "transcription": "AYB",
        "diplomatic": "ΜΝΗΣΘΗ",
        "translation": "Translated",
    }
    for layer, reading in expected.items():
        part = _textpart(api, layer)
        assert api.T.text(part, fmt="text-section-normalized-full") == reading
        if layer != "transcription":
            assert api.T.text(part, fmt="text-orig-full") == ""
    assert api.T.text(_textpart(api, "transcription"), fmt="text-orig-full") == "AYB"
    assert api.T.text(_textpart(api, "transcription"), fmt="text-layer-full") != "AYB"


def test_default_browser_displays_nonprimary_sections_without_adding_alternatives(
    native: tuple[Any, Any],
) -> None:
    assert "AYB" in _browse(native, "transcription")
    assert "X" not in _browse(native, "transcription")
    assert "ΜΝΗΣΘΗ" in _browse(native, "diplomatic")
    assert "Translated" in _browse(native, "translation")


def test_standard_browser_conf_declares_normalized_per_layer_default() -> None:
    config = (APP / "config.yaml").read_text(encoding="utf-8")
    assert "textFormat: text-section-normalized-full" in config


def test_source_critical_renderer_understands_normalized_section_format(
    native: tuple[Any, Any],
) -> None:
    from runpy import run_path
    from types import SimpleNamespace

    api, _ = native
    funcs = run_path(str(APP / "app.py"))
    primary = _textpart(api, "transcription")
    for slot in api.L.d(primary, otype="sign"):
        assert funcs["_is_selected_sign"](
            SimpleNamespace(api=api), slot, "text-section-normalized-full"
        ) == (api.F.reading_role.v(slot) in {"both", "normalized"})
