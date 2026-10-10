"""End-to-end native TF representation of pinned EpiDoc header provenance (#49)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import EdgeType, NodeType
from iip_tf.metadata_parser import MetadataParseError
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def _fixture(tmp_path: Path, xml: str, name: str = "iiptest.xml") -> Path:
    path = tmp_path / name
    path.write_text(xml, encoding="utf-8")
    return path


def test_project_contributors_and_publication_fields_survive_tf_roundtrip(
    tmp_path: Path,
) -> None:
    source = _fixture(
        tmp_path,
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"
          xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="record1">
          <teiHeader><fileDesc><titleStmt>
            <title>Source inscription title</title>
            <principal><persName xml:id="MS">Michael Satlow</persName></principal>
            <respStmt><resp>Prinicipal Investigator</resp>
              <persName xml:id="editor">Editor Name</persName></respStmt>
            <respStmt><resp xml:id="editor-role">Creator</resp><name>Another Author</name></respStmt>
          </titleStmt>
          <publicationStmt>
            <authority>Brown University</authority>
            <idno type="IIP">record1</idno>
            <availability status="free"><licence>Open licence
              <ref target="https://example.org/license">Licence Link</ref>
              <p>Attribution <ref>DOI reference</ref></p>
            </licence></availability>
          </publicationStmt></fileDesc></teiHeader>
          <text><body><div type="edition" subtype="transcription">
            <p>ABC</p>
          </div></body></text>
        </TEI>""",
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    inscription = ir.nodes_of_type(NodeType.INSCRIPTION)[0]
    assert inscription.feature("source_title") == "Source inscription title"
    assert inscription.feature("publication_authority") == "Brown University"

    responsibilities = ir.nodes_of_type(NodeType.RESPONSIBILITY)
    assert len(responsibilities) == 3
    assert [n.feature("responsibility_construct") for n in responsibilities] == [
        "principal", "respStmt", "respStmt"
    ]
    assert [n.feature("responsibility_role") for n in responsibilities] == [
        None, "Prinicipal Investigator", "Creator"
    ]
    assert [n.feature("agent_tag") for n in responsibilities] == [
        "persName", "persName", "name"
    ]
    assert [n.feature("agent_name") for n in responsibilities] == [
        "Michael Satlow", "Editor Name", "Another Author"
    ]
    assert [n.feature("agent_source_id") for n in responsibilities] == [
        "MS", "editor", None
    ]
    assert [n.feature("responsibility_role_source_id") for n in responsibilities] == [
        None, None, "editor-role"
    ]

    publication_id = ir.nodes_of_type(NodeType.PUBLICATION_ID)[0]
    assert publication_id.feature("publication_id_type") == "IIP"
    assert publication_id.feature("publication_id") == "record1"
    availability = ir.nodes_of_type(NodeType.PUBLICATION_AVAILABILITY)[0]
    licence = ir.nodes_of_type(NodeType.PUBLICATION_LICENCE)[0]
    refs = ir.nodes_of_type(NodeType.PUBLICATION_REFERENCE)
    paragraphs = ir.nodes_of_type(NodeType.PUBLICATION_PARAGRAPH)
    assert availability.feature("availability_status") == "free"
    assert licence.feature("licence_text") == (
        "Open licence Licence Link Attribution DOI reference"
    )
    assert len(refs) == 2
    assert len(paragraphs) == 1
    assert {n.feature("reference_target") for n in refs} == {
        "https://example.org/license", None
    }
    parents = {
        (edge.source, edge.target)
        for edge in ir.edges
        if edge.edge_type == EdgeType.PARENT
    }
    assert (licence.key, availability.key) in parents
    assert any((ref.key, paragraphs[0].key) in parents for ref in refs)

    dest = tmp_path / "tf"
    write_tf_corpus((ir,), dest, converter_commit="fixture-commit")
    api: Any = Fabric(locations=str(dest), silent=True).loadAll(silent=True)
    assert api
    F, E = api.F, api.E
    assert len(F.otype.s("responsibility")) == 3
    pi = next(
        n for n in F.otype.s("responsibility")
        if F.responsibility_role.v(n) == "Prinicipal Investigator"
    )
    assert F.agent_source_id.v(pi) == "editor"
    creator = next(n for n in F.otype.s("responsibility") if F.responsibility_role.v(n) == "Creator")
    assert F.responsibility_role_source_id.v(creator) == "editor-role"
    assert len(E.parent.f(pi)) == 1
    assert len(F.otype.s("publication_reference")) == 2
    assert len(F.otype.s("publication_paragraph")) == 1
    assert F.publication_authority.v(F.otype.s("inscription")[0]) == "Brown University"


def test_unresolved_include_and_empty_publication_identifier_are_retained(
    tmp_path: Path,
) -> None:
    source = _fixture(
        tmp_path,
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"
        xmlns:xi="http://www.w3.org/2001/XInclude">
        <teiHeader><fileDesc><titleStmt><title>Inscription</title>
          <respStmt><resp>Creator</resp><name xml:id="MS">Michael Satlow</name>
          </respStmt></titleStmt>
          <publicationStmt><xi:include href="https://example.org/publication.xml">
            <xi:fallback><p>ERROR-include missing</p></xi:fallback>
          </xi:include><idno/></publicationStmt>
        </fileDesc></teiHeader>
        <text><body><div type="edition" subtype="transcription"><p>A</p>
        </div></body></text></TEI>""",
    )
    ir = parse_epidoc_file(source, source_revision="fixture-revision")
    publication_id = ir.nodes_of_type(NodeType.PUBLICATION_ID)[0]
    assert publication_id.feature("publication_id") is None
    assert publication_id.feature("publication_id_type") is None
    include = ir.nodes_of_type(NodeType.PUBLICATION_INCLUDE)[0]
    assert include.feature("include_href") == "https://example.org/publication.xml"
    assert include.feature("include_fallback_text") == "ERROR-include missing"
    assert include.feature("include_resolved") == "0"
    assert ir.nodes_of_type(NodeType.RESPONSIBILITY)[0].feature("agent_source_id") == "MS"


@pytest.mark.parametrize(
    "fragment",
    [
        '<respStmt><resp>Creator</resp><name role="unexpected">A</name></respStmt>',
        '<respStmt><resp><hi>Creator</hi></resp><name>A</name></respStmt>',
        '<respStmt><resp>Creator</resp><name>A</name><orgName>X</orgName></respStmt>',
        '<respStmt><resp>Creator</resp><name>A</name><name>B</name></respStmt>',
    ],
)
def test_unmapped_contributor_shapes_fail_closed(
    tmp_path: Path, fragment: str
) -> None:
    xml = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc>'
        '<titleStmt><title>Title</title>' + fragment
        + '</titleStmt></fileDesc></teiHeader>'
        '<text><body><div type="edition" subtype="transcription"><p>A</p>'
        '</div></body></text></TEI>'
    )
    with pytest.raises(MetadataParseError):
        parse_epidoc_file(_fixture(tmp_path, xml), source_revision="fixture-revision")


def test_identical_agent_local_id_across_files_is_not_a_global_identity(
    tmp_path: Path,
) -> None:
    template = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader><fileDesc><titleStmt><title>Title</title>
        <respStmt><resp>Creator</resp><name xml:id="MS">Person</name></respStmt>
      </titleStmt></fileDesc></teiHeader>
      <text><body><div type="edition" subtype="transcription"><p>A</p>
      </div></body></text></TEI>"""
    one = parse_epidoc_file(
        _fixture(tmp_path, template, "one.xml"), source_revision="fixture-revision"
    )
    two = parse_epidoc_file(
        _fixture(tmp_path, template, "two.xml"), source_revision="fixture-revision"
    )
    a = one.nodes_of_type(NodeType.RESPONSIBILITY)[0]
    b = two.nodes_of_type(NodeType.RESPONSIBILITY)[0]
    assert a.feature("agent_source_id") == b.feature("agent_source_id") == "MS"
    assert a.key != b.key


def test_unsupported_publication_authority_markup_fails_closed(
    tmp_path: Path,
) -> None:
    source = _fixture(
        tmp_path,
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <teiHeader><fileDesc><titleStmt><title>Title</title></titleStmt>
          <publicationStmt>
            <authority><orgName>Brown University</orgName></authority>
            <idno type="IIP">one</idno>
          </publicationStmt></fileDesc></teiHeader>
          <text><body><div type="edition" subtype="transcription">
            <p>A</p></div></body></text>
        </TEI>""",
    )
    with pytest.raises(MetadataParseError, match="authority"):
        parse_epidoc_file(source, source_revision="fixture-revision")
