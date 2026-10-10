"""Command-line entry point for IIP-TF."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from iip_tf import __version__
from iip_tf.release_gate import inventory_source_files, require_empty_output_directory
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iip-tf",
        description="Convert the audited IIP EpiDoc source into native Text-Fabric.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")
    convert = subparsers.add_parser(
        "convert",
        help="parse a source directory and write one native Text-Fabric corpus",
    )
    convert.add_argument("source", type=Path)
    convert.add_argument("output", type=Path)
    convert.add_argument("--source-revision", required=True)
    convert.add_argument("--converter-commit", required=True)
    return parser


def _convert(args: argparse.Namespace) -> int:
    source: Path = args.source
    output: Path = args.output
    source_revision: str = args.source_revision
    converter_commit: str = args.converter_commit

    paths, _excluded = inventory_source_files(source, source_revision=source_revision)
    require_empty_output_directory(output)
    irs = tuple(
        parse_epidoc_file(path, source_revision=source_revision)
        for path in paths
    )
    write_tf_corpus(irs, output, converter_commit=converter_commit)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "convert":
        return _convert(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
