"""End-user smoke of a freshly extracted IIP-TF corpus, with no converter imports.

Execute under an isolated Python environment containing only Text-Fabric
and its ordinary dependencies: python -I scripts/smoke_researcher_archive.py PATH
"""
from __future__ import annotations

import argparse
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from tf.advanced.app import findApp  # type: ignore[import-untyped]
from tf.browser import kernel, web  # type: ignore[import-untyped]


def smoke_extracted_corpus(root: Path) -> None:
    root = root.resolve()
    tf_dir, app_dir = root / "tf", root / "app"
    if not (tf_dir / "otype.tf").is_file() or not (app_dir / "config.yaml").is_file():
        raise RuntimeError("extracted archive lacks native corpus or browser app")
    if find_spec("iip_tf") is not None:
        raise RuntimeError("smoke must run without an installed converter package")
    if any(root.rglob("*.xml")) or any(root.rglob("*.json")):
        raise RuntimeError("researcher distribution unexpectedly includes XML/JSON sidecars")

    # Use the browser's real production loader, which initializes provenance.
    app: Any = findApp(
        f"app:{app_dir}",
        None,
        None,
        "github",
        True,
        locations=str(tf_dir),
        silent="deep",
    )
    if app is None or app.api is None or not hasattr(app, "provenance"):
        raise RuntimeError("unpacked browser app could not load independently")
    api: Any = app.api
    if len(api.F.otype.s("inscription")) != 5535:
        raise RuntimeError("incomplete corpus loaded from extracted archive")
    for record_id in ("abil0001", "chor0001", "caes0260", "masa0286"):
        node = api.T.nodeFromSection((record_id,))
        if node is None or api.F.inscription_id.v(node) != record_id:
            raise RuntimeError(f"inscription navigation missing: {record_id}")
        if api.F.source_file.v(node) != f"{record_id}.xml":
            raise RuntimeError(f"source provenance missing: {record_id}")
    # This public-install acceptance also checks the researcher-to-source
    # journey. A local TF-only user must be able to follow the stable original
    # EpiDoc source without installing the converter or accessing a guessed URL.
    source_prefix = (
        "https://github.com/Brown-University-Library/iip-texts/blob/"
        "0b7dc8358ccdfd0c9391f049da4839fbd91c26e5/epidoc-files/"
    )
    for record_id in ("abil0001", "chor0001", "caes0260", "masa0286"):
        record = api.T.nodeFromSection((record_id,))
        assert record is not None
        expected_link = source_prefix + f"{record_id}.xml"
        if app.webLink(record, urlOnly=True) != expected_link:
            raise RuntimeError(f"archive has no source-faithful EpiDoc link: {record_id}")
        lines = api.L.d(record, otype="line")
        if not lines or app.webLink(lines[0], urlOnly=True) != expected_link:
            raise RuntimeError(f"archive passage source link is wrong: {record_id}")

    matches = tuple(api.S.search("inscription inscription_id=chor0001"))
    chor = api.T.nodeFromSection(("chor0001",))
    if chor is None or len(matches) != 1 or matches[0][0] != chor:
        raise RuntimeError("native TF indexed inscription search is broken")
    if not api.T.text(chor, fmt="text-orig-full").strip():
        raise RuntimeError("native original-text rendering is empty")

    browser_kernel = kernel.makeTfKernel(app, f"app:{app_dir}")
    webapp = web.factory(web.Web(browser_kernel))
    line = api.L.d(chor, otype="line")[0]
    textpart_section = api.T.sectionFromNode(line)[1]
    with webapp.test_client() as client:
        page = client.get("/")
        if page.status_code != 200:
            raise RuntimeError(f"unpacked browser homepage returned HTTP {page.status_code}")
        passage = client.post(
            "/passage",
            data={"sec0": "chor0001", "sec1": str(textpart_section)},
        )
        data = passage.get_json()
        if passage.status_code != 200 or not isinstance(data, dict) or not data.get("table"):
            raise RuntimeError("unpacked browser failed to render native passage")
        # A researcher must be able to click to the original Brown edition
        # directly from the downloaded archive's normal browser passage.
        # The native webLink API alone does not prove a rendered HTML anchor.
        expected_source = source_prefix + "chor0001.xml"
        passage_html = data["table"]
        if not isinstance(passage_html, str) or (
            f'href="{expected_source}"' not in passage_html
            or passage_html.count('class="iip-epidoc-link"') != 1
        ):
            raise RuntimeError(
                "unpacked browser passage lacks one clickable original EpiDoc link"
            )

    print(
        "Clean Text-Fabric-only installation: 5,535 native inscriptions; "
        "four source IDs; indexed search; original text; Flask / and /passage passed"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extracted_root", type=Path)
    args = parser.parse_args()
    smoke_extracted_corpus(args.extracted_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
