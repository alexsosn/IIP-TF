"""Command-line entry point for IIP-TF."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from iip_tf import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iip-tf",
        description=(
            "IIP-TF is under development. Conversion commands will be added "
            "only when their contracts are implemented and tested."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
