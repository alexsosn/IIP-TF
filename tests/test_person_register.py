"""#63 RED — real EpiDoc personal-name refs resolve only via pinned person register."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.cli import main as cli_main
from iip_tf.ir import EdgeType, NodeType
from iip_tf.person_register import (
    PersonRegisterError,
    attach_person_register,
    read_person_register,
)
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _register(tmp_path: Path, xml: str | None = None) -> Path:
    path = tmp_path / "persons.xml"
    path.write_text(
        xml or (
            '<listPerson>'
            '<person xml:id="beth0001p01" sex="1">'
            '<persName>Ioun</persName><faith>Jewish</faith></person>'
            '<person xml:id="beth0001p02" sex="2">'
            '<persName>Abra</persName><persName type="regularized">'
            'Abraham</persName><faith>Jewish-pagan</faith></person>'
            '<person xml:id="beth0001p03"><persName>Unknown</persName></person>'
            '</listPerson>'
        ),
        encoding="utf-8",
    )
    return path


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "beth0001.xml"
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<teiHeader><fileDesc><titleStmt><title>Names</title>'
        '<respStmt><resp>Editor</resp><name>'
        'Some Editor</name></respStmt></titleStmt>'
        '<sourceDesc><msDesc><msContents><textLang mainLang="grc"/>'
        '</msContents></msDesc></sourceDesc></fileDesc>'
        '<revisionDesc><change when="2020-01-01" who="persons.xml#editor123">'
        'Editor update</change></revisionDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription"><p>ΙΟΥΝ</p></div>'
        '<div type="translation"><p>'
        '<persName ref="persons.xml#beth0001p01" xml:lang="grc ">Ioun</persName> '
        '<persName ref="persons.xml#beth0001p02" xml:lang="hbo ">Abra</persName> '
        '<persName ref="persons.xml#beth0001p01">Ioun</persName> '
        '<persName ref="persons.xml#missing">Missing</persName> '
        '<persName ref="https://example.invalid#beth0001p03">Other</persName>'
        '</p></div></body></text></TEI>',
        encoding="utf-8",
    )
    return path


def test_person_register_links_canonical_entities_and_survives_tf_reload(
    tmp_path: Path,
) -> None:
    register = read_person_register(_register(tmp_path))
    original = parse_epidoc_file(_source(tmp_path), source_revision="fixture")
    assert not original.nodes_of_type(NodeType.PERSON)
    ir, audit = attach_person_register(original, register)
    people = ir.nodes_of_type(NodeType.PERSON)
    assert {node.feature("person_id") for node in people} == {
        "beth0001p01", "beth0001p02"
    }
    assert audit["resolved_entities"] == 3
    assert audit["distinct_people"] == 2
    assert audit["unresolved_targets"] == {"persons.xml#missing": 1}
    assert {(node.feature("person_name"), node.feature("sex"), node.feature("faith"))
            for node in people} == {
        ("Ioun", "1", "Jewish"),
        ("Abra", "2", "Jewish-pagan"),
    }
    abra = next(x for x in people if x.feature("person_id") == "beth0001p02")
    assert abra.feature("person_name_variants") == "Abraham"
    edges = [edge for edge in ir.edges if edge.edge_type == EdgeType.PERSON_REF]
    assert len(edges) == 3
    assert len({e.target for e in edges}) == 2
    assert all(e.source != e.target for e in edges)
    assert len(ir.signs) == len(original.signs)
    assert [s.glyph for s in ir.signs] == [s.glyph for s in original.signs]
    assert [(s.lang, s.lang_original) for s in ir.signs] == [
        (s.lang, s.lang_original) for s in original.signs
    ]

    out = tmp_path / "tf"
    write_tf_corpus((ir,), out, converter_commit="test-commit")
    api: Any = Fabric(locations=str(out), silent=True).loadAll(silent=True)
    assert api
    native_people = api.F.otype.s("person")
    assert len(native_people) == 2
    entity_to_person = api.E.person_ref
    assert sum(len(entity_to_person.f(n)) for n in api.F.otype.s("entity")) == 3
    assert {
        api.F.person_id.v(n): (api.F.sex.v(n), api.F.faith.v(n))
        for n in native_people
    } == {
        "beth0001p01": ("1", "Jewish"),
        "beth0001p02": ("2", "Jewish-pagan"),
    }
    for entity in api.F.otype.s("entity"):
        if api.F.ref.v(entity) == "persons.xml#beth0001p01":
            assert len(entity_to_person.f(entity)) == 1
            person = entity_to_person.f(entity)[0]
            assert api.F.person_id.v(person) == "beth0001p01"
    inscription = api.T.nodeFromSection(("beth0001",))
    assert inscription is not None
    assert "Ioun" in api.T.text(inscription, fmt="text-translation-full")


def test_no_person_fabricated_for_unlinked_register_or_contributors(
    tmp_path: Path,
) -> None:
    ir = parse_epidoc_file(_source(tmp_path), source_revision="fixture")
    enriched, report = attach_person_register(ir, read_person_register(_register(tmp_path)))
    assert len(enriched.nodes_of_type(NodeType.PERSON)) == 2
    assert "editor123" not in {n.feature("person_id") for n in enriched.nodes}
    assert "beth0001p03" not in {n.feature("person_id") for n in enriched.nodes}
    assert report["unresolved_targets"] == {"persons.xml#missing": 1}


def test_missing_sex_and_faith_stay_unset(tmp_path: Path) -> None:
    ir = parse_epidoc_file(_source(tmp_path), source_revision="fixture")
    target = next(n for n in ir.nodes if n.node_type == NodeType.ENTITY
                  and n.feature("ref") == "persons.xml#beth0001p01")
    updated = _register(
        tmp_path,
        '<listPerson><person xml:id="beth0001p01">'
        '<persName>Ioun</persName></person></listPerson>',
    )
    annotated, _ = attach_person_register(ir, read_person_register(updated))
    person = next(n for n in annotated.nodes_of_type(NodeType.PERSON))
    assert person.feature("sex") is None
    assert person.feature("faith") is None
    assert target.feature("ref") == "persons.xml#beth0001p01"


@pytest.mark.parametrize("xml", [
    '<listPerson><person xml:id="p" sex="9"><persName>A</persName></person></listPerson>',
    '<listPerson><person xml:id="p"><persName>A</persName></person>'
    '<person xml:id="p"><persName>B</persName></person></listPerson>',
    '<listPerson><person sex="1"><persName>A</persName></person></listPerson>',
    '<listPerson><person xml:id="p"><faith>Jewish</faith></person></listPerson>',
    '<listPerson><person xml:id="p"><persName>A</persName></person>',
])
def test_malformed_or_ambiguous_register_fails_closed(
    tmp_path: Path, xml: str,
) -> None:
    with pytest.raises(PersonRegisterError):
        read_person_register(_register(tmp_path, xml))


def test_person_id_must_belong_to_same_inscription(tmp_path: Path) -> None:
    ir = parse_epidoc_file(_source(tmp_path), source_revision="fixture")
    path = _register(
        tmp_path,
        '<listPerson><person xml:id="else0001p01">'
        '<persName>Ioun</persName></person></listPerson>',
    )
    enriched, report = attach_person_register(ir, read_person_register(path))
    assert enriched.nodes_of_type(NodeType.PERSON) == ()
    assert report["resolved_entities"] == 0
    assert "persons.xml#beth0001p01" in report["unresolved_targets"]


def test_empty_source_register_does_not_forge_link(tmp_path: Path) -> None:
    ir = parse_epidoc_file(_source(tmp_path), source_revision="fixture")
    path = _register(tmp_path, "<listPerson/>")
    enriched, audit = attach_person_register(ir, read_person_register(path))
    assert not enriched.nodes_of_type(NodeType.PERSON)
    assert not any(e.edge_type == EdgeType.PERSON_REF for e in enriched.edges)
    assert audit["resolved_entities"] == 0


def test_foreign_inscription_cannot_claim_another_record_person(
    tmp_path: Path,
) -> None:
    register = read_person_register(_register(tmp_path))
    ir = parse_epidoc_file(_source(tmp_path), source_revision="fixture")
    renamed = replace(ir, identity=replace(ir.identity, inscription_id="other0001"))
    linked, report = attach_person_register(renamed, register)
    assert linked.nodes_of_type(NodeType.PERSON) == ()
    assert not [e for e in linked.edges if e.edge_type == EdgeType.PERSON_REF]
    assert report["resolved_entities"] == 0
    assert report["unresolved_targets"]["persons.xml#beth0001p01"] == 2


def test_register_blob_authentication_rejects_altered_source(
    tmp_path: Path,
) -> None:
    path = _register(tmp_path)
    with pytest.raises(PersonRegisterError, match="blob mismatch"):
        read_person_register(path, expected_git_sha1="0" * 40)
    valid = read_person_register(path)
    assert len(valid) == 3
    assert "beth0001p01" in valid


def test_literal_reference_must_be_exact_not_fuzzy(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path)
    xml = source.read_text(encoding="utf-8").replace(
        'ref="persons.xml#beth0001p02"',
        'ref="persons.xml#beth0001p02 another.xml#beth0001p01"',
    )
    source.write_text(xml, encoding="utf-8")
    ir = parse_epidoc_file(source, source_revision="fixture")
    linked, report = attach_person_register(ir, read_person_register(_register(tmp_path)))
    assert len(linked.nodes_of_type(NodeType.PERSON)) == 1
    assert report["resolved_entities"] == 2
    assert report["unresolved_targets"][
        "persons.xml#beth0001p02 another.xml#beth0001p01"
    ] == 1


def test_cli_autodiscovers_sibling_brown_register(tmp_path: Path) -> None:
    source_dir = tmp_path / "epidoc-files"
    source_dir.mkdir()
    _source(source_dir)
    data_keep = tmp_path / "data-keep"
    data_keep.mkdir()
    _register(data_keep)

    output = tmp_path / "native"
    assert cli_main([
        "convert", str(source_dir), str(output),
        "--source-revision", "fixture",
        "--converter-commit", "test",
    ]) == 0
    api: Any = Fabric(locations=str(output), silent=True).loadAll(silent=True)
    assert len(api.F.otype.s("person")) == 2
    assert sum(len(api.E.person_ref.f(n)) for n in api.F.otype.s("entity")) == 3


def test_cli_requires_explicit_register_if_requested(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    _source(source)
    with pytest.raises(ValueError, match="persons register"):
        cli_main([
            "convert", str(source), str(tmp_path / "native"),
            "--source-revision", "fixture", "--converter-commit", "test",
            "--persons-register", str(tmp_path / "missing.xml"),
        ])
