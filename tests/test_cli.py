from __future__ import annotations

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
