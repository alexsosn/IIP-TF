"""Fail-closed six-file authenticated Brown IIP canary for pinned TF preflight.

This downloads no full corpus, caches no source XML and never changes the
mandatory authenticated full-corpus reproducibility/release gate.
"""

from __future__ import annotations

import hashlib
import re
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

PINNED_REVISION = "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5"
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "schema" / "pinned-canary-blobs.tsv"
SOURCE_BASE = (
    "https://raw.githubusercontent.com/Brown-University-Library/iip-texts/"
    f"{PINNED_REVISION}/epidoc-files/"
)
EXPECTED_CANARIES = frozenset(
    {
        "abil0001.xml",
        "bshe0146.xml",
        "caes0260.xml",
        "chor0001.xml",
        "haif0003.xml",
        "masa0286.xml",
    }
)
MAX_SOURCE_BYTES = 256_000


def git_blob_sha(content: bytes) -> str:
    """Return Git's SHA-1 *blob object* digest, not a raw-file SHA-1."""
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def verify_blob(filename: str, content: bytes, expected: str) -> None:
    """Reject untrusted bytes without leaking source XML in any diagnostic."""
    if len(content) > MAX_SOURCE_BYTES or not content:
        raise ValueError(f"{filename}: source blob exceeds allowed size or is empty")
    if git_blob_sha(content) != expected:
        raise ValueError(f"{filename}: pinned Git blob identity mismatch")


def read_manifest(path: Path) -> dict[str, str]:
    """Accept *only* the six preaudited filenames and immutable blob IDs."""
    result: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries = line.split("\t")
        if len(entries) != 2:
            raise ValueError(f"invalid pinned Git blob entry at line {line_number}")
        filename, digest = entries
        if not re.fullmatch(r"[a-z0-9]{4,20}\.xml", filename):
            raise ValueError(f"unsafe source filename at line {line_number}")
        if not re.fullmatch(r"[0-9a-f]{40}", digest):
            raise ValueError(f"invalid Git blob ID at line {line_number}")
        if filename in result:
            raise ValueError(f"duplicate pinned source filename: {filename}")
        result[filename] = digest
    if set(result) != EXPECTED_CANARIES or len(set(result.values())) != len(result):
        raise ValueError("incomplete or duplicated pinned source canary manifest")
    return result


def download_verified(
    manifest: Mapping[str, str],
    destination: Path,
    fetch: Callable[[str], bytes],
) -> tuple[Path, ...]:
    """Verify every blob *before writing* into a temporary data directory."""
    if set(manifest) != EXPECTED_CANARIES and set(manifest) != {"bshe0146.xml"}:
        raise ValueError("unexpected canary source set")
    destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename, digest in sorted(manifest.items()):
        if not re.fullmatch(r"[a-z0-9]{4,20}\.xml", filename):
            raise ValueError("unsafe source filename")
        if not re.fullmatch(r"[0-9a-f]{40}", digest):
            raise ValueError(f"{filename}: invalid pinned Git blob ID")
        raw = fetch(f"{SOURCE_BASE}{filename}")
        verify_blob(filename, raw, digest)
        target = destination / filename
        if target.exists():
            raise ValueError(f"{filename}: canary destination must be new")
        target.write_bytes(raw)
        paths.append(target)
    return tuple(paths)


def _fetch_bounded(url: str) -> bytes:
    """Bound download size and hanging network requests for fast preflight."""
    request = Request(url, headers={"User-Agent": "IIP-TF-authenticated-canary/0.1"})
    with urlopen(request, timeout=20) as stream:
        result: bytes = stream.read(MAX_SOURCE_BYTES + 1)
    if len(result) > MAX_SOURCE_BYTES:
        raise ValueError("source blob exceeds 256000-byte limit")
    return result


def _require_kind(api: Any, inscription_id: str, kinds: set[str]) -> None:
    owner = api.T.nodeFromSection((inscription_id,))
    if owner is None:
        raise RuntimeError(f"{inscription_id}: canary inscription not queryable")
    present = {api.F.kind.v(m) for m in api.L.d(owner, otype="markup")}
    if not kinds.issubset(present):
        raise RuntimeError(f"{inscription_id}: source markup canary failed")


def validate_real_canaries(files: tuple[Path, ...], output_dir: Path) -> None:
    """Parse, project segmentation, write and reload actual six source files."""
    if len(files) != len(EXPECTED_CANARIES):
        raise ValueError("must validate all six authenticated canary files")
    irs = tuple(
        parse_epidoc_file(path, source_revision=PINNED_REVISION)
        for path in sorted(files)
    )
    write_tf_corpus(irs, output_dir, converter_commit=PINNED_REVISION)
    api: Any = Fabric(locations=str(output_dir), silent=True).loadAll(silent=True)
    if api is None or len(api.F.otype.s("inscription")) != len(EXPECTED_CANARIES):
        raise RuntimeError("native TF canary record count or reload failed")

    _require_kind(api, "abil0001", {"supplied", "gap", "unclear"})
    _require_kind(api, "caes0260", {"abbr", "ex"})
    _require_kind(api, "masa0286", {"glyph"})
    _require_kind(api, "bshe0146", {"glyph"})

    for name, refs in {
        "masa0286": ("phoen-gaml", "phoen-delt"),
        "bshe0146": ("cross",),
    }.items():
        owner = api.T.nodeFromSection((name,))
        assert owner is not None
        native_refs = {
            api.F.ref.v(markup)
            for markup in api.L.d(owner, otype="markup")
            if api.F.kind.v(markup) == "glyph"
            and getattr(api.F, "annotation_source", None) is not None
            and api.F.annotation_source.v(markup) != "transcription_segmented"
        }
        # Unannotated source-markup values may have no annotation_source entry;
        # the optional node feature returns None for them.
        if not set(refs).issubset(native_refs):
            raise RuntimeError(f"{name}: authenticated source glyph refs changed")
        display = api.T.text(owner, fmt="text-orig-refs-full")
        if not all(f"(({ref}))" in display for ref in refs):
            raise RuntimeError(f"{name}: opt-in native display tokens missing")

    bshe = api.T.nodeFromSection(("bshe0146",))
    assert bshe is not None
    segmented_glyphs = [
        m for m in api.L.d(bshe, otype="markup")
        if api.F.kind.v(m) == "glyph"
        and api.F.annotation_source.v(m) == "transcription_segmented"
    ]
    if not segmented_glyphs:
        raise RuntimeError("bshe0146: projected segmented glyph not retained")

    chor = api.T.nodeFromSection(("chor0001",))
    assert chor is not None
    if not api.T.text(chor, fmt="text-orig-full").strip():
        raise RuntimeError("chor0001: ordinary primary reading missing")

    # Original Brown chor0001 has source paragraph xml:lang="heb" for
    # an Aramaic inscription written with Hebrew Unicode characters.
    hebrew_letters = [
        sign for sign in api.L.d(chor, otype="sign")
        if api.F.glyph.v(sign) and api.F.glyph.v(sign).isalpha()
        and api.F.layer.v(sign) == "transcription"
    ]
    if not hebrew_letters or any(
        api.F.script.v(sign) != "Hebr"
        or api.F.script_source.v(sign) != "encoded_unicode"
        for sign in hebrew_letters
    ):
        raise RuntimeError("chor0001: encoded Hebrew script evidence lost")
    # The original source p@xml:lang=heb still belongs in lang_original,
    # while selected native Aramaic words now correct effective sign language.
    original = [
        sign for sign in hebrew_letters
        if api.F.lang_original.v(sign) == "heb"
        and api.F.lang_origin.v(sign) == "p"
    ]
    if len(original) < 10:
        raise RuntimeError("chor0001: original EpiDoc lang provenance changed")
    corrected = [
        sign for sign in original
        if api.F.lang.v(sign) == "arc"
        and api.F.lang_source.v(sign) == "transcription_segmented"
    ]
    if len(corrected) < 10:
        raise RuntimeError("chor0001: projected word language not applied to source letters")
    caes = api.T.nodeFromSection(("caes0260",))
    if caes is None:
        raise RuntimeError("caes0260: missing real Greek inscription")
    greek_letters = [
        sign for sign in api.L.d(caes, otype="sign")
        if api.F.glyph.v(sign) and api.F.glyph.v(sign).isalpha()
        and api.F.layer.v(sign) == "transcription"
    ]
    if not greek_letters or any(api.F.script.v(sign) != "Grek" for sign in greek_letters):
        raise RuntimeError("caes0260: encoded Greek script evidence lost")
    haif = api.T.nodeFromSection(("haif0003",))
    assert haif is not None
    diplomatic_parts = [
        n for n in api.L.d(haif, otype="textpart")
        if api.F.layer.v(n) == "diplomatic"
    ]
    if not diplomatic_parts or not any(
        api.T.text(n, fmt="text-diplomatic-full").strip() for n in diplomatic_parts
    ):
        raise RuntimeError("haif0003: nonprimary diplomatic text missing")

    print("Authenticated Brown IIP canary: six sources and native TF assertions passed")


def main() -> int:
    manifest = read_manifest(MANIFEST)
    with tempfile.TemporaryDirectory(prefix="iip-pinned-canary-") as working:
        root = Path(working)
        paths = download_verified(manifest, root / "epidoc-files", _fetch_bounded)
        validate_real_canaries(paths, root / "native-tf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
