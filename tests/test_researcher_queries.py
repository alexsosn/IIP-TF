"""Executable researcher documentation contract (#9, RED before implementation)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.researcher_queries import inspect_corpus, require_native_features
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


@pytest.fixture
def native_api(tmp_path: Path) -> Any:
    source = tmp_path / "sample.xml"
    source.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><titleStmt><title>Example</title>'
        '<respStmt><resp>Editor</resp><name>Recorder</name></respStmt>'
        '</titleStmt><publicationStmt><idno>sample</idno></publicationStmt>'
        '</fileDesc></teiHeader>'
        '<text><body>'
        '<div type="edition" subtype="transcription"><p>'
        'A<supplied reason="lost" cert="low">B</supplied>'
        '<gap reason="lost" unit="character" extent="unknown"/>C'
        '</p></div>'
        '<div type="translation"><p>Example translation.</p></div>'
        '</body></text></TEI>',
        encoding="utf-8",
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    tf_dir = tmp_path / "native-tf"
    write_tf_corpus((ir,), tf_dir, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(tf_dir), silent=True).loadAll(silent=True)
    assert api
    return api


def test_researcher_quickstart_runs_real_text_fabric_queries(native_api: Any) -> None:
    result = inspect_corpus(native_api, ("sample",))
    assert result["inscription_count"] == 1
    assert result["source_revision"] == "fixture-revision"
    assert result["data_licence"] == "CC BY-NC 4.0"
    record = result["records"][0]
    assert record["inscription_id"] == "sample"
    assert record["search_hits"] == 1
    assert "ABC" in record["primary_text"]
    assert "Example translation." in record["translation_text"]
    assert "gap" in record["markup_kinds"]
    assert "supplied" in record["markup_kinds"]
    assert record["line_count"] >= 1
    assert "inscription_id" in result["node_features"]
    assert "parent" in result["edge_features"]
    assert isinstance(json.dumps(result, ensure_ascii=False), str)


def test_missing_inscription_fails_instead_of_lying_with_empty_text(native_api: Any) -> None:
    with pytest.raises(ValueError, match="not found"):
        inspect_corpus(native_api, ("nonexistent",))


def test_misspelled_documented_feature_must_fail(native_api: Any) -> None:
    with pytest.raises(ValueError, match="missing native TF"):
        require_native_features(native_api, ("inscripton_id",))


def test_researcher_guide_command_links_to_executable_entrypoint() -> None:
    root = Path(__file__).resolve().parents[1]
    guide = (root / "docs/guides/researcher-quickstart.md").read_text(
        encoding="utf-8"
    )
    assert "python -m iip_tf.researcher_queries" in guide
    assert "abil0001" in guide
    assert "caes0260" in guide
    assert "masa0286" in guide
    assert "CC BY-NC 4.0" in guide
    assert "No released" in guide or "not yet released" in guide
    assert "TF_DIR" not in guide  # every copied command is self-contained
