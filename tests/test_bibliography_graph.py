"""#62 RED: globally shared, source-attested native TF cited-publication graph."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.bibliography_index import read_bibliography_index
from iip_tf.ir import (
    EdgeType,
    InscriptionIR,
    IREdge,
    IRNode,
    IRSign,
    Layer,
    NodeType,
    SourceIdentity,
    SourceProvenance,
)
from iip_tf.tf_writer import write_tf_corpus

REV = "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"


def _authority(path: Path) -> Path:
    path.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><listBibl>'
        '<biblStruct type="document"><monogr>'
        '<title level="m">A Catalogue of Jewish Ossuaries</title>'
        '<idno type="callNumber">IIP-119</idno>'
        '<author><forename>L.Y.</forename><surname>Rahmani</surname></author>'
        '<editor><forename>Ayala</forename><surname>Sussmann</surname></editor>'
        '<imprint><publisher>Israel Antiquities Authority</publisher>'
        '<date>1994</date></imprint></monogr></biblStruct>'
        '<biblStruct type="journalArticle"><analytic>'
        '<title level="a">Tombeau et Ossuaires Juifs</title>'
        '<author><forename>F.-M</forename><surname>Abel</surname></author>'
        '<author><name>et. al.</name></author>'
        '</analytic><monogr><title level="j">Revue Biblique</title>'
        '<imprint><date>1913</date></imprint></monogr><note type="tags">'
        '<note type="tag" xml:id="IIP-001">IIP-001</note>'
        '<note type="tag" xml:id="IIP-694">IIP-694</note>'
        '</note></biblStruct>'
        '<biblStruct type="book"><monogr><title level="m">Uncited work</title>'
        '<idno type="callNumber">IIP-999</idno></monogr></biblStruct>'
        '</listBibl></body></text></TEI>',
        encoding="utf-8",
    )
    return path


def _record(name: str, *targets: str | None) -> InscriptionIR:
    sign_key = f"{name}#s1"
    sign = IRSign(sign_key, "A", Layer.TRANSCRIPTION)
    inscription = f"{name}#record"
    textpart = f"{name}#textpart"
    line = f"{name}#line"
    nodes = [
        IRNode(
            inscription, NodeType.INSCRIPTION, (sign_key,),
            (("inscription_id", name), ("source_file", f"{name}.xml"),
             ("primary_layer", "transcription")),
        ),
        IRNode(
            textpart, NodeType.TEXTPART, (sign_key,),
            (("layer", "transcription"), ("section_part", "transcription")),
        ),
        IRNode(
            line, NodeType.LINE, (sign_key,),
            (("layer", "transcription"), ("line_n", 1)),
        ),
    ]
    edges = [
        IREdge(EdgeType.PARENT, textpart, inscription),
        IREdge(EdgeType.PARENT, line, textpart),
    ]
    for ordinal, target in enumerate(targets, start=1):
        bibl_key = f"{name}#bibl{ordinal}"
        features: tuple[tuple[str, str | int], ...] = (
            (("target", target),) if target is not None else ()
        )
        nodes.append(IRNode(bibl_key, NodeType.BIBL, (sign_key,), features))
        edges.append(IREdge(EdgeType.PARENT, bibl_key, inscription))
        edges.append(IREdge(EdgeType.IN_INSCRIPTION, bibl_key, inscription))
    return InscriptionIR(
        identity=SourceIdentity(name, f"{name}.xml", name, (), "grc"),
        provenance=SourceProvenance(REV, False, None, 0),
        signs=(sign,),
        nodes=tuple(nodes),
        edges=tuple(edges),
        diagnostics=(),
    )


def _load(path: Path) -> Any:
    api = Fabric(locations=str(path), silent=True).loadAll(silent=True)
    assert api
    return api


def _tf_bytes(path: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in path.glob("*.tf")}


def _write_with_authority(*args: Any, **kwargs: Any) -> None:
    # RED-first: production writer has not acquired the authority argument yet.
    write: Any = write_tf_corpus
    write(*args, **kwargs)


def test_real_native_shared_publications_and_repeatable_authorities(
    tmp_path: Path,
) -> None:
    index = read_bibliography_index(_authority(tmp_path / "zotero.xml"))
    records = (
        _record("aaa0001", "IIP-119.xml", "IIP-694.xml", "IIP-0119.xml"),
        _record("bbb0002", "IIP-119.xml", "IIP-001", "SEG", None),
    )
    native = tmp_path / "tf"
    _write_with_authority(records, native, converter_commit="test", bibliography_index=index)
    api = _load(native)
    F, E = api.F, api.E

    publications = tuple(F.otype.s("publication"))
    assert len(publications) == 2  # not a publication per citation or alias
    rahmani = tuple(F.publication_key.s("IIP-119"))[0]
    abel = tuple(F.publication_key.s("IIP-001"))[0]
    assert set(publications) == {rahmani, abel}
    assert F.publication_title.v(rahmani) == "A Catalogue of Jewish Ossuaries"
    assert F.publication_monograph_title.v(rahmani) == "A Catalogue of Jewish Ossuaries"
    assert F.publication_analytic_title.v(rahmani) is None
    assert F.publication_date.v(rahmani) == "1994"
    assert F.publication_publisher.v(rahmani) == "Israel Antiquities Authority"
    assert F.publication_analytic_title.v(abel) == "Tombeau et Ossuaires Juifs"
    assert F.publication_monograph_title.v(abel) == "Revue Biblique"
    assert F.publication_date.v(abel) == "1913"
    assert F.publication_source_blob.v(rahmani) == index.source_git_blob

    bibl_rahmani = tuple(F.target.s("IIP-119.xml"))
    assert len(bibl_rahmani) == 2
    assert all(tuple(E.publication_ref.f(b)) == (rahmani,) for b in bibl_rahmani)
    assert set(E.publication_ref.t(rahmani)) == set(bibl_rahmani)
    assert set(E.oslots.s(rahmani)) == set().union(
        *(set(E.oslots.s(b)) for b in bibl_rahmani)
    )
    owners = {F.inscription_id.v(E.in_inscription.f(b)[0]) for b in bibl_rahmani}
    assert owners == {"aaa0001", "bbb0002"}
    assert not E.in_inscription.f(rahmani)  # no fabricated unique owner

    assert tuple(E.publication_ref.f(F.target.s("IIP-694.xml")[0])) == (abel,)
    assert tuple(E.publication_ref.f(F.target.s("IIP-001")[0])) == (abel,)
    for unknown in ("IIP-0119.xml", "SEG"):
        assert tuple(E.publication_ref.f(F.target.s(unknown)[0])) == ()
    assert len(F.otype.s("publication")) == 2  # uncited IIP-999 absent

    keys = tuple(F.otype.s("publication_key"))
    assert {
        (F.publication_alias_key.v(n), E.parent.f(n)[0])
        for n in keys
    } == {
        ("IIP-119", rahmani), ("IIP-001", abel), ("IIP-694", abel),
    }
    agents = tuple(F.otype.s("publication_agent"))
    assert {
        (F.publication_agent_surname.v(n), F.publication_agent_role.v(n),
         F.publication_agent_order.v(n), E.parent.f(n)[0])
        for n in agents
    } == {
        ("Rahmani", "author", 1, rahmani),
        ("Sussmann", "editor", 1, rahmani),
        ("Abel", "author", 1, abel),
        (None, "author", 2, abel),
    }
    assert any(F.publication_agent_name.v(n) == "et. al." for n in agents)
    assert api.T.text(api.T.nodeFromSection(("aaa0001",)), fmt="text-orig-full") == "A"
    assert api.T.text(api.T.nodeFromSection(("bbb0002",)), fmt="text-orig-full") == "A"
    assert list(api.S.search("publication publication_date=1994")) == [(rahmani,)]


def test_publication_graph_is_deterministic_under_ir_input_reordering(
    tmp_path: Path,
) -> None:
    index = read_bibliography_index(_authority(tmp_path / "zotero.xml"))
    irs = (
        _record("zzz0002", "IIP-119.xml", "IIP-001.xml"),
        _record("aaa0001", "IIP-694", "IIP-119"),
    )
    first, second = tmp_path / "first", tmp_path / "second"
    _write_with_authority(irs, first, converter_commit="test", bibliography_index=index)
    _write_with_authority(reversed(irs), second, converter_commit="test", bibliography_index=index)
    assert _tf_bytes(first) == _tf_bytes(second)


def test_standalone_without_authority_keeps_original_source_bibl(
    tmp_path: Path,
) -> None:
    path = tmp_path / "tf"
    write_tf_corpus((_record("aaa0001", "IIP-119.xml"),), path, converter_commit="test")
    api = _load(path)
    assert tuple(api.F.otype.s("publication")) == ()
    assert tuple(api.F.target.s("IIP-119.xml"))
    assert api.T.text(api.T.nodeFromSection(("aaa0001",)), fmt="text-orig-full") == "A"
