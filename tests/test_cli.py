from __future__ import annotations

from pathlib import Path

import pytest

from iip_tf import __version__
from iip_tf.cli import main


def test_version_flag_reports_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"iip-tf {__version__}"


def test_empty_cli_is_a_successful_bootstrap_smoke() -> None:
    assert main([]) == 0


def test_cli_rejects_nonempty_output_before_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "real0001.xml").write_text("<TEI/>", encoding="utf-8")
    output = tmp_path / "valuable"
    output.mkdir()
    existing = output / "otype.tf"
    existing.write_text("preserve previous corpus", encoding="utf-8")

    def forbidden_parse(*args: object, **kwargs: object) -> None:
        raise AssertionError("must reject output before parsing a source file")

    monkeypatch.setattr("iip_tf.cli.parse_epidoc_file", forbidden_parse)
    with pytest.raises(ValueError, match="not empty"):
        main([
            "convert", str(source), str(output),
            "--source-revision", "test-other-upstream",
            "--converter-commit", "test-commit",
        ])
    assert existing.read_text(encoding="utf-8") == "preserve previous corpus"
