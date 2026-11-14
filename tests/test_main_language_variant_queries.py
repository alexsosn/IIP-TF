"""#52 RED-first: exact source-language variants as native inscription queries."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest
from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


@pytest.fixture
def language_api(tmp_path: Path) -> Any:
    records = (
        ("demo0001", "he"),
        ("demo0002", "heb"),
        ("demo0003", "la"),
        ("demo0004", "lat"),
        ("demo0005", "geo"),
        ("demo0006", "Geo"),
        ("demo0007", "arc"),
        ("demo0008", "Other"),
    )
    irs = []
    for stem, code in records:
        path = tmp_path / f"{stem}.xml"
        path.write_text(
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader><fileDesc><titleStmt><title>Fixture</title></titleStmt>'
            '<sourceDesc><msDesc><msContents>'
            f'<textLang mainLang="{code}"/>'
            '</msContents></msDesc></sourceDesc>'
            '</fileDesc></teiHeader><text><body>'
            '<div type="edition" subtype="transcription"><p>A</p></div>'
            '</body></text></TEI>',
            encoding="utf-8",
        )
        irs.append(parse_epidoc_file(path, source_revision="fixture-revision"))
    target = tmp_path / "tf"
    write_tf_corpus(tuple(irs), target, converter_commit="test")
    api: Any = Fabric(locations=str(target), silent=True).loadAll(silent=True)
    assert api
    return api


def test_alias_union_returns_native_inscription_nodes_without_source_coercion(
    language_api: Any,
) -> None:
    find = importlib.import_module(
        "iip_tf.researcher_queries"
    ).find_inscriptions_by_main_language
    he = find(language_api, "heb")
    assert tuple(language_api.F.inscription_id.v(n) for n in he) == (
        "demo0001", "demo0002",
    )
    assert tuple(language_api.F.main_lang.v(n) for n in he) == ("he", "heb")
    assert set(he) == (
        set(language_api.F.main_lang.s("he"))
        | set(language_api.F.main_lang.s("heb"))
    )
    assert len(he) == len(set(he))


def test_latin_and_georgian_variants_are_scoped_only_to_source_main_lang(
    language_api: Any,
) -> None:
    find = importlib.import_module(
        "iip_tf.researcher_queries"
    ).find_inscriptions_by_main_language
    for iso3, ids in (
        ("lat", {"demo0003", "demo0004"}),
        ("kat", {"demo0005", "demo0006"}),
    ):
        nodes = find(language_api, iso3)
        assert {language_api.F.inscription_id.v(n) for n in nodes} == ids
        assert all(language_api.F.otype.v(n) == "inscription" for n in nodes)
    assert not (
        set(find(language_api, "heb")) & set(find(language_api, "kat"))
    )


def test_unknown_unclassified_codes_fail_closed_without_guessing(
    language_api: Any,
) -> None:
    find = importlib.import_module(
        "iip_tf.researcher_queries"
    ).find_inscriptions_by_main_language
    for unsupported in ("Other", "x-unknown", "arc-Grek", "heb-Grek", "Heb"):
        with pytest.raises(ValueError, match="unsupported"):
            find(language_api, unsupported)
    assert find(language_api, "heb") != ()
    assert language_api.F.main_lang.s("Other")
    # We deliberately do not alias word or sign language: container 'heb'
    # in Aramaic records can describe writing system, not text language.
