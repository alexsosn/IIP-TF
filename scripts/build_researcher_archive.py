"""Build a source-free IIP-TF researcher archive from an authenticated native build.

Only release maintainers run this script. Its output is ordinary Text-Fabric
data and the standard local browser app, independent of the converter at use.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import tarfile
from pathlib import Path

from iip_tf.release_gate import tf_feature_hashes
from iip_tf.source_repair import PINNED_IIP_REVISION

ROOT = Path(__file__).resolve().parents[1]
APP_FILES = ("app.py", "config.yaml", "static/display.css")
REQUIRED_TF_FILES = frozenset({"otype.tf", "oslots.tf", "otext.tf"})

# This travels in the archive. It is guidance, not a TF semantic sidecar.
START_HERE = f"""IIP-TF: local Text-Fabric corpus
================================

This archive contains a converted, source-attributed native Text-Fabric
dataset and the standard TF browser app. Brown EpiDoc/XML and the IIP-TF
converter are NOT required to read it.

Original IIP source revision: {PINNED_IIP_REVISION}
Original source: https://github.com/Brown-University-Library/iip-texts
IIP project DOI: https://doi.org/10.26300/pz1d-st89
Data licence: CC BY-NC 4.0; preserve source-edition and contributor credit.
See LICENSE_SCOPE.md for attribution and licence boundaries.
The local browser app is covered by the accompanying MIT software licence.

INSTALL FROM THE DIRECTORY CONTAINING THE DOWNLOADED ARCHIVE:
  mkdir iip-tf-data
  tar -xzf iip-tf-corpus.tar.gz -C iip-tf-data
  cd iip-tf-data
  python -m pip install 'text-fabric>=13.1,<14'

OPEN THE STANDARD LOCAL BROWSER:
  python -m tf.browser.start "app:$(pwd)/app" "--locations=$(pwd)/tf" -noweb

The command prints a local browser address. Open it on your machine and
end the process using Ctrl-C. No browser service or corpus data are hosted
by this archive.

QUERY THE NATIVE CORPUS IN PYTHON FROM THE EXTRACTED DIRECTORY:
  from tf.fabric import Fabric
  api = Fabric(locations="tf", silent=True).loadAll()
  assert api is not None
  node = api.T.nodeFromSection(("abil0001",))
  print(api.T.text(node, fmt="text-orig-full"))
  print(tuple(api.S.search("inscription inscription_id=abil0001")))

The browser can display editorial notes and reviewed Unicode/fallback
labels, but these presentation annotations are not source letters.
Inspect original source text and native TF feature provenance for citation.
The native TF feature headers retain source and converter identities.
This archive contains no upstream XML, image binaries, or semantic JSON.
"""


def _validated_sources(tf_dir: Path, report_path: Path) -> dict[str, Path | bytes]:
    """Refuse packaging anything other than the complete authenticated native build."""
    if tf_dir.is_symlink() or not tf_dir.is_dir():
        raise ValueError("native TF directory is missing or a symlink")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("status") != "success":
        raise ValueError("archive requires a successful pinned build report")
    if report.get("source_revision") != PINNED_IIP_REVISION:
        raise ValueError("source revision is not the authenticated Brown pin")
    converter = report.get("converter_commit")
    if not isinstance(converter, str) or not converter.strip():
        raise ValueError("archive requires explicit converter identity")
    source_files = report.get("source_files")
    if not isinstance(source_files, dict):
        raise ValueError("archive requires source-file accounting")
    converted = source_files.get("converted")
    if (
        not isinstance(converted, list)
        or len(converted) != 5535
        or len(set(converted)) != 5535
        or source_files.get("failed") != []
    ):
        raise ValueError("archive requires 5,535 unique converted records and zero failures")

    # The existing double-build validator has already certified these exact
    # hashes. Check them against the bytes being packaged, not against a
    # separate or re-built corpus. Disposable TF caches are never shipped.
    actual_hashes = tf_feature_hashes(tf_dir)
    if not REQUIRED_TF_FILES.issubset(actual_hashes):
        raise ValueError("native TF warp/config features are missing")
    if report.get("tf_feature_hashes") != actual_hashes:
        raise ValueError("TF feature bytes disagree with authenticated build report")
    sources: dict[str, Path | bytes] = {}
    for name in sorted(actual_hashes):
        path = tf_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"symlink or invalid TF feature: {name}")
        sources[f"tf/{name}"] = path

    for name in APP_FILES:
        path = ROOT / "app" / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing or linked browser app file: {name}")
        sources[f"app/{name}"] = path
    for name in ("LICENSE", "LICENSE_SCOPE.md"):
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing required attribution file: {name}")
        sources[name] = path
    sources["START_HERE.txt"] = START_HERE.encode("utf-8")
    return sources


def build_researcher_archive(
    tf_dir: Path, report_path: Path, destination: Path
) -> Path:
    """Make a repeatable .tar.gz with TF data, app, licence and setup instructions.

    Never replace or clear an existing path. This does not publish a release.
    """
    if destination.is_symlink() or destination.exists():
        raise FileExistsError(f"refusing to replace existing archive: {destination}")
    sources = _validated_sources(tf_dir, report_path)
    try:
        with destination.open("xb") as output:
            with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as zipped:
                with tarfile.open(fileobj=zipped, mode="w") as archive:
                    for name in sorted(sources):
                        source = sources[name]
                        info = tarfile.TarInfo(name=name)
                        info.mode = 0o644
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        info.mtime = 0
                        if isinstance(source, bytes):
                            info.size = len(source)
                            archive.addfile(info, io.BytesIO(source))
                        else:
                            info.size = source.stat().st_size
                            with source.open("rb") as stream:
                                archive.addfile(info, stream)
    except Exception:
        # Only our newly created output can be removed, never previous user data.
        destination.unlink(missing_ok=True)
        raise
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tf_dir", type=Path)
    parser.add_argument("build_report", type=Path)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    result = build_researcher_archive(args.tf_dir, args.build_report, args.archive)
    print(f"Source-free researcher archive candidate: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
