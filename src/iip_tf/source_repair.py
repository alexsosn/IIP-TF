"""Fail-closed repair for the seven malformed files in the pinned IIP source."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

PINNED_IIP_REVISION = "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"
REPAIR_ID = "iip-2024-facsimile-conflict-union-v1"

_START = "<<<<<<< Updated upstream"
_MIDDLE = "======="
_END = ">>>>>>> Stashed changes"

_REPAIRS: dict[str, tuple[str, str]] = {
    "bqut0002.xml": (
        """<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes""",
        "",
    ),
    "caes0433.xml": (
        """<<<<<<< Updated upstream
=======
            <desc/>
>>>>>>> Stashed changes""",
        "            <desc/>",
    ),
    "sepp0018.xml": (
        """<<<<<<< Updated upstream
         <desc>Zev Radovan</desc>
         <graphic url="sepp0018.jpg"/>
=======
      <graphic url="sepp0018.jpg"/>
      <!-- <graphic url="images/thumbnails/i_sepp0018_t.jpg"/> -->
>>>>>>> Stashed changes""",
        """         <desc>Zev Radovan</desc>
         <graphic url="sepp0018.jpg"/>
      <!-- <graphic url="images/thumbnails/i_sepp0018_t.jpg"/> -->""",
    ),
    "sepp0019.xml": (
        """<<<<<<< Updated upstream
      <!-- <graphic url="images/thumbnails/i_sepp0018_t.jpg"/> -->
=======

>>>>>>> Stashed changes""",
        '      <!-- <graphic url="images/thumbnails/i_sepp0018_t.jpg"/> -->',
    ),
    "sepp0020.xml": (
        """<<<<<<< Updated upstream
=======
      <!-- <graphic url="images/thumbnails/i_sepp0020_t.jpg"/> -->
>>>>>>> Stashed changes""",
        '      <!-- <graphic url="images/thumbnails/i_sepp0020_t.jpg"/> -->',
    ),
    "sepp0021.xml": (
        """<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes""",
        "",
    ),
    "sepp0024.xml": (
        """<<<<<<< Updated upstream
      <!-- <graphic url="images/thumbnails/i_sepp0024_t.jpg"/> -->
=======
      <desc>Zev Radovan</desc>
>>>>>>> Stashed changes""",
        """      <!-- <graphic url="images/thumbnails/i_sepp0024_t.jpg"/> -->
      <desc>Zev Radovan</desc>""",
    ),
}


class SourceConflictError(ValueError):
    """Raised when source repair would require an unresearched choice."""


@dataclass(frozen=True)
class SourceRepairResult:
    """Result of validating or repairing one source file."""

    text: str
    repaired: bool
    repair_id: str | None
    filename: str
    source_revision: str
    conflict_count: int


@dataclass(frozen=True)
class DirectoryValidationResult:
    """Accounting for a source-directory validation pass."""

    total_xml: int
    well_formed: int
    repaired: int
    repaired_files: tuple[str, ...]
    failures: tuple[str, ...]


def _validate_xml(text: str, *, filename: str) -> None:
    try:
        ET.fromstring(text)
    except ET.ParseError as exc:
        raise SourceConflictError(f"{filename}: malformed XML: {exc}") from exc


def repair_source_file(path: Path, *, source_revision: str) -> SourceRepairResult:
    """Validate one source file and apply a researched pinned-revision repair if needed."""

    text = path.read_text(encoding="utf-8")
    filename = path.name
    conflict_count = text.count(_START)

    if conflict_count == 0:
        if _MIDDLE in text or _END in text:
            raise SourceConflictError(f"{filename}: incomplete Git conflict markers")
        _validate_xml(text, filename=filename)
        return SourceRepairResult(
            text=text,
            repaired=False,
            repair_id=None,
            filename=filename,
            source_revision=source_revision,
            conflict_count=0,
        )

    if source_revision != PINNED_IIP_REVISION:
        raise SourceConflictError(
            f"{filename}: conflict repair is allowed only for the pinned IIP revision "
            f"{PINNED_IIP_REVISION}"
        )

    rule = _REPAIRS.get(filename)
    if rule is None:
        raise SourceConflictError(f"{filename}: no researched conflict repair exists")

    expected, replacement = rule
    marker_shape_ok = (
        conflict_count == 1
        and text.count(_MIDDLE) == 1
        and text.count(_END) == 1
        and text.count(expected) == 1
    )
    if not marker_shape_ok:
        raise SourceConflictError(f"{filename}: source no longer matches researched conflict block")

    repaired = text.replace(expected, replacement, 1)
    if _START in repaired or _MIDDLE in repaired or _END in repaired:
        raise SourceConflictError(f"{filename}: conflict markers remain after researched repair")

    _validate_xml(repaired, filename=filename)
    return SourceRepairResult(
        text=repaired,
        repaired=True,
        repair_id=REPAIR_ID,
        filename=filename,
        source_revision=source_revision,
        conflict_count=conflict_count,
    )


def validate_source_directory(
    source_dir: Path,
    *,
    source_revision: str,
) -> DirectoryValidationResult:
    """Validate every top-level XML file and account for all researched repairs."""

    paths = sorted(source_dir.glob("*.xml"))
    repaired_files: list[str] = []
    failures: list[str] = []

    for path in paths:
        try:
            result = repair_source_file(path, source_revision=source_revision)
        except SourceConflictError as exc:
            failures.append(str(exc))
            continue
        if result.repaired:
            repaired_files.append(path.name)

    return DirectoryValidationResult(
        total_xml=len(paths),
        well_formed=len(paths) - len(failures),
        repaired=len(repaired_files),
        repaired_files=tuple(repaired_files),
        failures=tuple(failures),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m iip_tf.source_repair",
        description="Validate IIP XML and apply only researched pinned-source repairs.",
    )
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expect-total", type=int)
    parser.add_argument("--expect-repairs", type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_source_directory(args.source_dir, source_revision=args.revision)
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))

    if report.failures:
        return 1
    if args.expect_total is not None and report.total_xml != args.expect_total:
        return 1
    if args.expect_repairs is not None and report.repaired != args.expect_repairs:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
