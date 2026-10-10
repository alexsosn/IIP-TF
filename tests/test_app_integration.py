"""RED/green tests for standard native TF app bootstrap (#8)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from tf.app import use  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def test_app_config_uses_only_documented_advanced_tf_settings() -> None:
    config = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
    assert config["apiVersion"] == 3
    assert config["dataDisplay"]["textFormat"] == "text-orig-full"
    assert config["provenanceSpec"]["corpus"]
    assert config["provenanceSpec"]["org"] == "alexsosn"
    assert config["provenanceSpec"]["repo"] == "IIP-TF"
    assert config["typeDisplay"]["inscription"]["label"] == "{inscription_id}"
    assert config["typeDisplay"]["line"]["label"] == "{line_n}"


def test_advanced_app_can_wrap_native_tf_data_offline(tmp_path: Path) -> None:
    source = tmp_path / "minimal.xml"
    source.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Sample</title>"
        "<respStmt><resp>Creator</resp><name>Editor</name></respStmt>"
        "</titleStmt><publicationStmt><idno>minimal</idno></publicationStmt>"
        "</fileDesc></teiHeader>"
        '<text><body><div type="edition" subtype="transcription">'
        "<p>ABC</p></div></body></text></TEI>",
        encoding="utf-8",
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    data_dir = tmp_path / "native-tf"
    write_tf_corpus((ir,), data_dir, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(data_dir), silent=True).loadAll(silent=True)
    assert api

    # Local app and preloaded native data: no network, no published corpus.
    app: Any = use(f"app:{APP}", api=api, silent="deep")
    assert app is not None
    assert app.api.F.otype.s("inscription")
    inscription = app.api.F.otype.s("inscription")[0]
    assert app.api.F.inscription_id.v(inscription) == "minimal"
    assert app.api.T.text(inscription, fmt="text-orig-full").strip() == "ABC"
    line = app.api.F.otype.s("line")[0]
    rendered = app.plain(line, _asString=True)
    assert isinstance(rendered, str)
    assert "ABC" in rendered
