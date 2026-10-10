"""Pinned IIP-TF app + browser smoke, against already verified native TF data.

Runs after validate_pinned_tf.py; never downloads data or interprets EpiDoc.
"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from tf.advanced.app import findApp  # type: ignore[import-untyped]
from tf.browser import kernel, web  # type: ignore[import-untyped]

from iip_tf.researcher_queries import verify_pinned_examples

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

    # Load through TF's production browser-mode app loader, not by passing
    # a preloaded Fabric API. The latter bypasses its module/provenance setup
    # (app.provenance), which is required by the HTML index route.
    # This also loads 1.47M slots only once, avoiding memory amplification.
    app: Any = findApp(
        f"app:{APP_DIR}",
        None,
        None,
        "github",
        True,
        locations=str(args.tf_dir.resolve()),
        silent="deep",
    )
    if app is None or app.api is None or not hasattr(app, "provenance"):
        raise RuntimeError("pinned browser loader did not initialize native TF")
    api: Any = app.api

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

        # These are actual browser endpoints, not just core TF section lookups.
        # A three-level corpus with browseNavLevel=2 requires both the
        # inscription (sec0) and textpart (sec1) for line content.
        sections = api.L.d(chor, otype="line")
        if not sections:
            raise RuntimeError("pinned inscription has no browseable line")
        section = api.T.sectionFromNode(sections[0])
        passage = client.post(
            "/passage", data={"sec0": "chor0001", "sec1": str(section[1])}
        )
        payload = passage.get_json()
        if passage.status_code != 200 or not isinstance(payload, dict):
            raise RuntimeError("pinned browser passage endpoint failed")
        if not isinstance(payload.get("table"), str) or not payload["table"]:
            raise RuntimeError("pinned browser returned empty passage HTML")

        search = client.post(
            "/query",
            data={"query": "inscription inscription_id=abil0001", "condenseType": "line"}
        )
        query_payload = search.get_json()
        if (
            search.status_code != 200
            or not isinstance(query_payload, dict)
            or query_payload.get("status") is not True
            or query_payload.get("nResults") != 1
        ):
            raise RuntimeError(f"pinned browser exact-ID search failed: {query_payload!r}")
    # Source-critical reading: choose the textpart containing the actual
    # editorial node, not a guessed section index or a synthetic placeholder.
    for record_id, kind, expected in (
        ("abil0001", "gap", "gap"),
        ("abil0001", "supplied", "supplied"),
        ("caes0260", "ex", "ex"),
        ("masa0286", "glyph", "phoen-gaml"),
    ):
        owner = api.T.nodeFromSection((record_id,))
        if owner is None:
            raise RuntimeError(f"missing pinned editorial record: {record_id}")
        markups = [
            m for m in api.L.d(owner, otype="markup")
            if api.F.kind.v(m) == kind
        ]
        if not markups:
            raise RuntimeError(f"{record_id}: missing source editorial kind={kind}")
        target_line = next(
            (
                line
                for m in markups
                for line in api.L.u(m, otype="line")
                if api.F.layer.v(m) == api.F.primary_layer.v(owner)
            ),
            None,
        )
        if target_line is None:
            raise RuntimeError(f"{record_id}: no primary text line for {kind}")
        textpart = api.T.sectionFromNode(target_line)[1]
        with webapp.test_client() as client:
            endpoint = client.post(
                "/passage", data={"sec0": record_id, "sec1": str(textpart)}
            )
        if endpoint.status_code != 200:
            raise RuntimeError(f"{record_id}: editorial browser route not HTTP 200")
        endpoint_data = endpoint.get_json()
        html = endpoint_data.get("table") if isinstance(endpoint_data, dict) else None
        if not isinstance(html, str):
            raise RuntimeError(f"{record_id}: missing passage HTML")
        visible_note = VisibleText()
        visible_note.feed(html)
        if expected not in " ".join(visible_note.parts):
            raise RuntimeError(
                f"{record_id}: {kind} source evidence invisible in browser"
            )
    research_results = verify_pinned_examples(api)
    print(
        "Researcher examples verified: "
        + ", ".join(row["inscription_id"] for row in research_results["records"])
    )
    print("Pinned TF app: 5,535 sections; reference glyph preserved; HTTP / = 200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
