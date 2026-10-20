"""#11 RED-first: Agora host must preserve Brown authorities and the actual TF browser."""

from __future__ import annotations

import json
import socket
import tomllib
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

import iip_tf.agora as agora_module
from iip_tf.person_register import git_blob_sha1
from iip_tf.release_gate import git_source_tree_sha
from iip_tf.taxonomy_audit import PINNED_SOURCE_REVISION, git_blob_sha
from iip_tf.agora import main, materialize

ROOT = Path(__file__).resolve().parents[1]


def _source(root: Path) -> Path:
    source = root / "brown"
    epidoc = source / "epidoc-files"
    keep = source / "data-keep"
    epidoc.mkdir(parents=True)
    keep.mkdir(parents=True)
    (epidoc / "demo0001.xml").write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><titleStmt><title>Agora test</title></titleStmt>'
        '<sourceDesc><msDesc><msContents><textLang mainLang="grc"/>'
        '<msItem class="#dedicatory" ana="#jewish"><p/></msItem>'
        '</msContents></msDesc></sourceDesc></fileDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription">'
        '<p>ΑΒ</p></div><div type="translation"><p>'
        '<persName ref="persons.xml#demo0001p01" xml:lang="grc">Abba</persName>'
        '</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    names = {
        "IIP-form": ("block", "Block"),
        "IIP-materials": ("stone", "Stone"),
        "IIP-genre": ("dedicatory", "Dedicatory"),
        "IIP-preservation": ("complete", "Complete"),
        "IIP-writing": ("painted", "Painted"),
        "IIP-religion": ("jewish", "Jewish"),
    }
    xml = "".join(
        f'<taxonomy xml:id="{name}"><category xml:id="{cat}">'
        f'<catDesc>{label}</catDesc></category></taxonomy>'
        for name, (cat, label) in names.items()
    )
    (source / "include_taxonomies.xml").write_text(
        '<classDecl xmlns="http://www.tei-c.org/ns/1.0">'
        + xml + "</classDecl>", encoding="utf-8",
    )
    (keep / "persons.xml").write_text(
        '<listPerson><person xml:id="demo0001p01" sex="1">'
        '<persName>Abba</persName><faith>Jewish</faith></person></listPerson>',
        encoding="utf-8",
    )
    return source


def test_approved_existing_empty_staging_preserves_real_source_to_tf(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    output = tmp_path / "staging"
    output.mkdir()
    with patch.object(socket, "create_connection", side_effect=AssertionError("network used")):
        result = materialize(source, output, source_revision="")
    assert result == output / "tf"
    assert {x.name for x in output.iterdir()} == {"tf", "app", "conversion-summary.json"}
    for name in ("otype.tf", "oslots.tf", "otext.tf"):
        assert (output / "tf" / name).is_file()

    api: Any = Fabric(locations=str(result), silent=True).loadAll(silent=True)
    record = api.T.nodeFromSection(("demo0001",))
    assert record is not None
    assert api.F.genre.v(record) == "dedicatory"
    assert api.F.genre_original.v(record) == "#dedicatory"
    assert api.F.religion.v(record) == "jewish"
    assert api.F.religion_original.v(record) == "#jewish"
    assert len(api.F.otype.s("person")) == 1
    person = api.F.otype.s("person")[0]
    assert api.F.person_id.v(person) == "demo0001p01"
    assert api.F.faith.v(person) == "Jewish"
    assert sum(len(api.E.person_ref.f(e)) for e in api.F.otype.s("entity")) == 1
    assert "ΑΒ" in api.T.text(record, fmt="text-orig-full")
    assert api.F.inscription_id.meta["license"] == "CC BY-NC 4.0"
    assert api.F.inscription_id.meta["sourceCommit"] == "unversioned-local"
    assert api.F.inscription_id.meta["converterCommit"].startswith("sha256:")

    report = json.loads((output / "conversion-summary.json").read_text())
    assert report["source_revision"] == "unversioned-local"
    assert report["source_revision_verified"] is False
    assert report["tf_path"] == "tf"
    assert report["app_path"] == "app"
    assert report["converter_content_sha256"].startswith("sha256:")
    assert str(tmp_path) not in (output / "conversion-summary.json").read_text()


def test_packaged_browser_app_is_byte_identical_to_upstream_app(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    materialize(source, output, source_revision="fixture")
    for relative in ("app.py", "config.yaml", "static/display.css"):
        assert (output / "app" / relative).read_bytes() == (
            ROOT / "app" / relative
        ).read_bytes()


def test_bad_source_does_not_silently_drop_taxonomies_or_people(tmp_path: Path) -> None:
    source = _source(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    for path in (source / "include_taxonomies.xml", source / "data-keep/persons.xml"):
        original = path.read_bytes()
        path.unlink()
        with pytest.raises(ValueError, match="required Brown source"):
            materialize(source, output, source_revision="fixture")
        assert list(output.iterdir()) == []
        path.write_bytes(original)


def test_occupied_and_symlink_output_fail_without_overwriting(tmp_path: Path) -> None:
    source = _source(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("never replace")
    with pytest.raises(ValueError, match="empty"):
        materialize(source, output, source_revision="fixture")
    assert sentinel.read_text() == "never replace"
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        materialize(source, link, source_revision="fixture")
    assert list(outside.iterdir()) == []


def test_cli_exits_failure_without_network_or_false_artifact(tmp_path: Path) -> None:
    source = _source(tmp_path)
    (source / "data-keep/persons.xml").unlink()
    output = tmp_path / "staging"
    output.mkdir()
    assert main([str(source), str(output), "--source-revision", ""]) != 0
    assert list(output.iterdir()) == []



def test_local_exact_pinned_source_without_git_metadata_is_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source(tmp_path)
    monkeypatch.setattr(
        agora_module, "PINNED_EPIDOC_SOURCE_TREE",
        git_source_tree_sha(source / "epidoc-files"),
    )
    monkeypatch.setattr(
        agora_module, "PINNED_TAXONOMY_BLOB",
        git_blob_sha((source / "include_taxonomies.xml").read_bytes()),
    )
    monkeypatch.setattr(
        agora_module, "PINNED_PERSONS_BLOB",
        git_blob_sha1(source / "data-keep/persons.xml"),
    )
    output = tmp_path / "verified"
    output.mkdir()
    materialize(source, output, source_revision="")
    report = json.loads((output / "conversion-summary.json").read_text())
    assert report["source_revision"] == PINNED_SOURCE_REVISION
    assert report["source_revision_verified"] is True
    api: Any = Fabric(locations=str(output / "tf"), silent=True).loadAll(silent=True)
    assert api.F.inscription_id.meta["sourceCommit"] == PINNED_SOURCE_REVISION


def test_unverified_source_with_known_brown_test_fixture_is_not_ingested(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    test_file = source / "epidoc-files/aaTestFile.xml"
    test_file.write_bytes((source / "epidoc-files/demo0001.xml").read_bytes())
    output = tmp_path / "staging"
    output.mkdir()
    with pytest.raises(ValueError, match="aaTestFile|unverified"):
        materialize(source, output, source_revision="")
    assert list(output.iterdir()) == []

def test_manifest_targets_full_brown_root_and_real_python_module() -> None:
    manifest = json.loads((ROOT / "agora.materializer.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert manifest["schema_version"] == 1
    assert manifest["plugin"]["id"] == "iip-tf"
    assert manifest["plugin"]["version"] == project["version"]
    assert manifest["plugin"]["repository"] == "alexsosn/IIP-TF"
    assert len(manifest["materializers"]) == 1
    entry = manifest["materializers"][0]
    git, local = entry["acquisition"]
    assert git["type"] == "git"
    assert git["subpath"] == "."
    assert git["ref"] == "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"
    assert git["url"] == "https://github.com/Brown-University-Library/iip-texts.git"
    assert local["type"] == "user-local"
    assert entry["input"] == {
        "type": "directory",
        "required_globs": [
            "epidoc-files/*.xml",
            "include_taxonomies.xml",
            "data-keep/persons.xml",
        ],
        "allow_symlinks": False,
    }
    assert entry["execution"] == {
        "type": "python-module", "module": "iip_tf.agora",
        "args": ["{source}", "{output}", "--source-revision", "{source_revision}"],
        "network": "deny",
    }
    assert entry["output"]["format"] == "text-fabric"
    assert set(entry["output"]["required_paths"]) == {
        "tf/otype.tf", "tf/oslots.tf", "tf/otext.tf",
        "app/app.py", "app/config.yaml", "app/static/display.css",
        "conversion-summary.json",
    }
