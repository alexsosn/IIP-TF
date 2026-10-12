"""Command-line entry point for IIP-TF."""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from pathlib import Path

from iip_tf import __version__
from iip_tf.ir import InscriptionIR
from iip_tf.person_register import attach_person_register, read_person_register
from iip_tf.release_gate import inventory_source_files, require_empty_output_directory
from iip_tf.taxonomy_audit import (
    PINNED_SOURCE_REVISION,
    PINNED_TAXONOMY_BLOB,
    parse_taxonomies,
)
from iip_tf.taxonomy_resolution import resolve_taxonomy_features
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
    convert.add_argument("--persons-register", type=Path)
    convert.add_argument("--taxonomy-file", type=Path)
    return parser


def _convert(args: argparse.Namespace) -> int:
    source: Path = args.source
    output: Path = args.output
    source_revision: str = args.source_revision
    converter_commit: str = args.converter_commit

    paths, _excluded = inventory_source_files(source, source_revision=source_revision)
    register_path = args.persons_register or (source.parent / "data-keep" / "persons.xml")
    register = read_person_register(register_path) if register_path.is_file() else None
    if args.persons_register is not None and register is None:
        raise ValueError(f"explicit persons register does not exist: {register_path}")
    taxonomy_path = args.taxonomy_file or (source.parent / "include_taxonomies.xml")
    taxonomy = (
        parse_taxonomies(
            taxonomy_path.read_bytes(),
            expected_blob=PINNED_TAXONOMY_BLOB
            if source_revision == PINNED_SOURCE_REVISION else None,
        )
        if taxonomy_path.is_file() else None
    )
    if args.taxonomy_file is not None and taxonomy is None:
        raise ValueError(f"explicit taxonomy source does not exist: {taxonomy_path}")
    require_empty_output_directory(output)
    def records() -> Iterator[InscriptionIR]:
        for path in paths:
            ir = parse_epidoc_file(path, source_revision=source_revision)
            if taxonomy is not None:
                ir, _taxonomy_audit = resolve_taxonomy_features(ir, taxonomy)
            yield attach_person_register(ir, register)[0] if register is not None else ir

    irs = tuple(records())
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
