"""Research #49 invariants against source-like EpiDoc responsibility variants."""

from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf.source_repair import PINNED_IIP_REVISION
from scripts.research_issue49_responsibilities import audit


def test_responsibility_inventory_retains_repetition_and_external_publication(
    tmp_path: Path,
) -> None:
    (tmp_path / "idum0001.xml").write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"
        xmlns:xi="http://www.w3.org/2001/XInclude">
          <teiHeader><fileDesc>
            <titleStmt><title>IIP</title>
              <respStmt><resp>Prinicipal Investigator</resp>
                <persName xml:id="MS">Michael Satlow</persName></respStmt>
              <respStmt><resp>Creator</resp>
                <name xml:id="MS">Michael Satlow</name></respStmt>
              <respStmt><resp>Editor</resp><name>E. Scholar</name>
                <orgName>Unmodeled contributor organization</orgName></respStmt>
            </titleStmt>
            <publicationStmt><authority>Brown University</authority></publicationStmt>
          </fileDesc></teiHeader>
        </TEI>""",
        encoding="utf-8",
    )
    (tmp_path / "akld0001.xml").write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"
        xmlns:xi="http://www.w3.org/2001/XInclude">
          <teiHeader><fileDesc>
            <publicationStmt><xi:include href="../publication.xml"/></publicationStmt>
          </fileDesc></teiHeader>
        </TEI>""",
        encoding="utf-8",
    )

    report = audit(tmp_path, revision=PINNED_IIP_REVISION, expected_records=2)
    counts = report["counts"]
    assert report["parsed"] == 2
    assert counts["records_with_titleStmt"] == 1
    assert counts["records_without_titleStmt"] == 1
    assert counts["records_with_multiple_respStmt"] == 1
    assert counts["respStmt_count"] == 3
    assert counts["agent_tag:persName"] == 1
    assert counts["agent_tag:name"] == 2
    assert counts["publication_authority_text:Brown University"] == 1
    assert counts["unexpanded_publication_xinclude"] == 1
    assert report["role_counts"]["Prinicipal Investigator"] == 1
    assert report["role_counts"]["Creator"] == 1
    assert any("orgName" in anomaly["other_children"] for anomaly in report["anomalies"])
    assert any(
        "{http://www.tei-c.org/ns/1.0}persName" in shape
        for shape in report["title_and_agent_shapes"]
    )


def test_responsibility_inventory_rejects_incomplete_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unexpected parsed source count"):
        audit(tmp_path, revision=PINNED_IIP_REVISION, expected_records=1)
