"""Offline Agora adapter for the complete Brown IIP source and standard TF app.

Agora owns acquisition, managed installation, sandbox, network denial, and
publication. This module only validates inputs and delegates semantics to the
existing standalone IIP-TF converter, exporting the existing TF browser.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from iip_tf import __version__
from iip_tf.cli import main as convert_cli
from iip_tf.person_register import PINNED_PERSONS_BLOB, git_blob_sha1
from iip_tf.release_gate import (
    PINNED_EPIDOC_SOURCE_TREE,
    ReproducibilityError,
    require_source_tree_sha,
)
from iip_tf.taxonomy_audit import (
    PINNED_SOURCE_REVISION,
    PINNED_TAXONOMY_BLOB,
    parse_taxonomies,
)

UNVERSIONED_LOCAL = "unversioned-local"
_APP_FILES = ("app.py", "config.yaml", "static/display.css")


def _software_fingerprint() -> str:
    """Stable content identity of installed converter and browser resources.

    Agora removes Git metadata before installing plugins. This is explicitly
    *not* a Git commit; Agora's separate receipt binds the immutable plugin
    commit and code installation.
    """
    root = Path(__file__).resolve().parent
    files = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix in {".py", ".yaml", ".css"}),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    if not files:
        raise ValueError("installed IIP-TF code resources are missing")
    digest = hashlib.sha256()
    for file in files:
        relative = file.relative_to(root).as_posix().encode("utf-8")
        content = file.read_bytes()
        digest.update(relative + b"\0" + len(content).to_bytes(8, "big") + content)
    return "sha256:" + digest.hexdigest()


def _required_source(root: Path) -> tuple[Path, Path, Path]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"required Brown source root must be a real directory: {root}")
    transcription = root / "epidoc-files"
    taxonomy = root / "include_taxonomies.xml"
    persons = root / "data-keep" / "persons.xml"
    if any(path.is_symlink() for path in (transcription, taxonomy, persons, persons.parent)):
        raise ValueError("required Brown source paths must not be symlinks")
    if not transcription.is_dir() or not taxonomy.is_file() or not persons.is_file():
        raise ValueError(
            "required Brown source: epidoc-files/, include_taxonomies.xml, "
            "and data-keep/persons.xml must all be present"
        )
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"required Brown source cannot contain symlinks: {path}")
    return transcription, taxonomy, persons


def materialize(source: Path, output: Path, *, source_revision: str) -> Path:
    """Write native TF + original app to an existing empty Agora staging root."""
    if output.is_symlink() or not output.is_dir():
        raise ValueError("Agora output must be an existing non-symlink directory")
    if any(output.iterdir()):
        raise ValueError("Agora output must be empty before conversion")
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError("Agora output must not reside within its Brown source root")

    transcription, taxonomy, persons = _required_source(source)
    requested_revision = source_revision
    pinned = False
    if not requested_revision or requested_revision == PINNED_SOURCE_REVISION:
        # A downloaded Brown snapshot with no .git is still authentically the
        # pin when the *three consumed source components* match their hashes.
        # This also keeps aaTestFile.xml excluded by the existing converter.
        try:
            require_source_tree_sha(transcription, expected_sha=PINNED_EPIDOC_SOURCE_TREE)
            parse_taxonomies(taxonomy.read_bytes(), expected_blob=PINNED_TAXONOMY_BLOB)
            if git_blob_sha1(persons) != PINNED_PERSONS_BLOB:
                raise ValueError("pinned Brown persons.xml Git blob mismatch")
        except (ReproducibilityError, TaxonomyError, ValueError) as exc:
            if requested_revision == PINNED_SOURCE_REVISION:
                raise ValueError("pinned Brown source components do not match") from exc
        else:
            pinned = True
    source_revision = (
        PINNED_SOURCE_REVISION if pinned
        else requested_revision or UNVERSIONED_LOCAL
    )
    # This is an attested upstream test fixture, excluded only for authenticated
    # pinned Brown content. An unverified local copy must not silently turn it
    # into an inscription, regardless of the revision text supplied by the host.
    if not pinned and (transcription / "aaTestFile.xml").exists():
        raise ValueError(
            "unverified Brown source contains aaTestFile.xml; "
            "refusing to convert a known non-inscription fixture"
        )

    bundled = Path(__file__).resolve().parent / "_bundled_app"
    for relative in _APP_FILES:
        if not (bundled / relative).is_file() or (bundled / relative).is_symlink():
            raise ValueError(f"missing installed TF browser resource: {relative}")
    fingerprint = _software_fingerprint()

    # Reuse the standalone public converter path, with no Agora branch in its
    # parser, IR, taxonomy or Text-Fabric writer semantics.
    result = convert_cli([
        "convert", str(transcription), str(output / "tf"),
        "--source-revision", source_revision,
        "--converter-commit", fingerprint,
    ])
    if result != 0:
        raise RuntimeError(f"standalone IIP-TF conversion returned {result}")

    app_dir = output / "app"
    for relative in _APP_FILES:
        target = app_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bundled / relative, target)

    summary = {
        "status": "success",
        "source_repository": "Brown-University-Library/iip-texts",
        "source_revision": source_revision,
        "source_revision_verified": pinned,
        "converter_version": __version__,
        "converter_content_sha256": fingerprint,
        "tf_path": "tf",
        "app_path": "app",
        "data_license": "CC BY-NC 4.0",
        "source_doi": "10.26300/pz1d-st89",
    }
    (output / "conversion-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output / "tf"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a local IIP Text-Fabric corpus using Agora's prepared Brown source."
    )
    parser.add_argument("source", type=Path, help="Brown iip-texts root, not epidoc-files/")
    parser.add_argument("output", type=Path, help="Existing, empty Agora staging directory")
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args(argv)
    try:
        materialize(args.source, args.output, source_revision=args.source_revision)
    except Exception as exc:
        print(f"IIP-TF materialization failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
