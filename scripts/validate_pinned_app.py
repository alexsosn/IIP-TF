"""Pinned IIP-TF app + browser smoke, against already verified native TF data.

Runs after validate_pinned_tf.py; never downloads data or interprets EpiDoc.
"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from tf.app import use  # type: ignore[import-untyped]
from tf.browser import kernel, web  # type: ignore[import-untyped]
from tf.fabric import Fabric  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tf_dir", type=Path)
    args = parser.parse_args()

    api: Any = Fabric(locations=str(args.tf_dir.resolve()), silent=True).loadAll(
        silent=True
    )
    if not api:
        raise RuntimeError("pinned app validation could not load native TF")
    app: Any = use(f"app:{APP_DIR}", api=api, silent="deep")
    if app is None or app.api is None:
        raise RuntimeError("pinned app could not wrap native TF API")

    if len(api.F.otype.s("inscription")) != 5535:
        raise RuntimeError("pinned app did not load 5,535 inscriptions")

    for source_id in ("abil0001", "chor0001", "caes0260", "masa0286"):
        node = api.T.nodeFromSection((source_id,))
        if node is None or api.F.inscription_id.v(node) != source_id:
            raise RuntimeError(f"native IIP section navigation failed: {source_id}")

    chor = api.T.nodeFromSection(("chor0001",))
    assert chor is not None
    content = api.T.text(chor, fmt="text-orig-full")
    if not content.strip():
        raise RuntimeError("Aramaic-source inscription lost its visible TF text")

    # Empty Phoenician glyph references remain source-queryable, even though
    # default display is an acknowledged limitation tracked in #58.
    masada = api.T.nodeFromSection(("masa0286",))
    assert masada is not None
    native_refs = [
        api.F.ref.v(markup)
        for markup in api.L.d(masada, otype="markup")
        if api.F.kind.v(markup) == "glyph"
    ]
    if "phoen-gaml" not in native_refs:
        raise RuntimeError("paleo-Hebrew inscription glyph reference was lost")

    # Exercise real native browser route creation and returned HTML against the
    # full corpus, without spawning another process or loading the corpus twice.
    browser_kernel = kernel.makeTfKernel(app, f"app:{APP_DIR}")
    webapp = web.factory(web.Web(browser_kernel))
    with webapp.test_client() as client:
        response = client.get("/")
        if response.status_code != 200:
            raise RuntimeError(f"TF browser failed: HTTP {response.status_code}")
        text = VisibleText()
        text.feed(response.get_data(as_text=True))
        if "IIP" not in "".join(text.parts) and "Inscriptions" not in "".join(
            text.parts
        ):
            raise RuntimeError("TF browser response lacks IIP corpus identity")
    print("Pinned TF app: 5,535 sections; reference glyph preserved; HTTP / = 200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
