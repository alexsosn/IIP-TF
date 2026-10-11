"""Pinned IIP-TF app + browser smoke, against already verified native TF data.

Runs after validate_pinned_tf.py; never downloads data or interprets EpiDoc.
"""

from __future__ import annotations

import argparse
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
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



def validate_native_reference_tokens(api: Any) -> int:
    """Verify all source-backed primary glyph-reference tokens, not a sample."""
    F, L = api.F, api.L
    annotation_source = getattr(F, "annotation_source", None)
    matched = 0
    for slot in F.synthetic_kind.s("glyph_ref"):
        if F.glyph.v(slot) is not None:
            raise RuntimeError(f"glyph reference slot {slot} gained fabricated source text")
        glyph_markups = [
            node for node in L.u(slot, otype="markup")
            if F.kind.v(node) == "glyph"
            and not (
                annotation_source is not None
                and annotation_source.v(node) == "transcription_segmented"
            )
        ]
        if len(glyph_markups) != 1:
            raise RuntimeError(f"glyph ref slot {slot} has ambiguous/missing native markup")
        source_ref = F.ref.v(glyph_markups[0])
        owners = L.u(slot, otype="inscription")
        if len(owners) != 1:
            raise RuntimeError(f"glyph ref slot {slot} lacks unique inscription owner")
        primary = (
            F.layer.v(slot) == F.primary_layer.v(owners[0])
            and F.reading_role.v(slot) in {"both", "normalized"}
        )
        expected = (
            f"(({escape(source_ref, quote=True)}))"
            if primary and source_ref else None
        )
        actual = F.primary_ref_token.v(slot)
        if actual != expected:
            raise RuntimeError(
                f"glyph reference slot {slot}: expected {expected!r}, actual {actual!r}"
            )
        if expected:
            matched += 1

    if matched < 1000:
        raise RuntimeError(f"unexpectedly low pinned primary glyph-ref coverage: {matched}")

    for record_id, expected_refs in (
        ("masa0286", ("phoen-gaml", "phoen-delt")),
        ("masa0290", ("phoen-wau", "phoen-mem")),
    ):
        owner = api.T.nodeFromSection((record_id,))
        if owner is None:
            raise RuntimeError(f"missing native glyph-reference example: {record_id}")
        plain = api.T.text(owner, fmt="text-orig-full")
        with_refs = api.T.text(owner, fmt="text-orig-refs-full")
        if plain.strip():
            raise RuntimeError(f"{record_id} unexpectedly contains visible source glyphs")
        for ref in expected_refs:
            if f"(({ref}))" not in with_refs:
                raise RuntimeError(f"{record_id}: missing opt-in glyph ref {ref}")
    print(f"Pinned native glyph-reference display: {matched} primary tokens verified")
    return matched


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

    validate_native_reference_tokens(api)

    # The opt-in ref view uses precisely the primary normalized sign
    # selection and must not suppress source-critical notes in the TF app.
    # Exercise the production custom renderer against REAL Brown source
    # slots, before creating the Flask browser, with no second TF load.
    custom = getattr(app, "customMethods", None)
    plain_custom = getattr(custom, "plainCustom", {}) if custom is not None else {}
    render_sign = plain_custom.get("sign")
    if render_sign is None:
        raise RuntimeError("IIP native browser sign renderer unavailable")
    options = SimpleNamespace(fmt="text-orig-refs-full")
    glyph_nodes = [
        node for node in api.L.d(masada, otype="markup")
        if api.F.kind.v(node) == "glyph" and api.F.ref.v(node) == "phoen-gaml"
    ]
    if len(glyph_nodes) != 1:
        raise RuntimeError("pinned Masada primary source ref not unique")
    glyph_slot = api.E.oslots.s(glyph_nodes[0])[0]
    glyph_html = render_sign(options, (glyph_slot,), "sign", False)
    if "glyph ref=phoen-gaml" not in glyph_html or "((phoen-gaml))" not in glyph_html:
        raise RuntimeError("opt-in native glyph label/reading not rendered")

    abil = api.T.nodeFromSection(("abil0001",))
    if abil is None:
        raise RuntimeError("pinned source critical inscription missing")
    supplied = [
        node for node in api.L.d(abil, otype="markup")
        if api.F.kind.v(node) == "supplied"
        and api.F.layer.v(node) == api.F.primary_layer.v(abil)
    ]
    if not supplied:
        raise RuntimeError("pinned primary supplied text evidence missing")
    supplied_slot = api.E.oslots.s(supplied[0])[0]
    supplied_html = render_sign(options, (supplied_slot,), "sign", False)
    if "⟦supplied" not in supplied_html:
        raise RuntimeError("opt-in source-reference view suppressed supplied note")

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
    # Nonprimary section browser visibility, grounded in pinned Brown
    # EpiDoc. The core TF default remains the primary-only source view;
    # the browser must instead show the chosen textpart's normalized layer.
    if api.T.defaultFormat != "text-orig-full":
        raise RuntimeError("core TF default primary reading changed unexpectedly")
    for record_id, layer, source_snippet in (
        ("haif0003", "diplomatic", "ΜΝΗΣΘΗ"),
        ("bloy0002", "translation", "Moriah"),
    ):
        owner = api.T.nodeFromSection((record_id,))
        if owner is None:
            raise RuntimeError(f"{record_id}: missing pinned nonprimary record")
        if api.F.primary_layer.v(owner) == layer:
            raise RuntimeError(f"{record_id}: expected {layer} to be nonprimary")
        textparts = [
            n for n in api.L.d(owner, otype="textpart")
            if api.F.layer.v(n) == layer
        ]
        matches = [
            line for part in textparts for line in api.L.d(part, otype="line")
            if source_snippet in api.T.text(
                line, fmt="text-section-normalized-full"
            )
        ]
        if not matches:
            raise RuntimeError(
                f"{record_id}: existing {layer} text missing from normalized layer format"
            )
        target_line = matches[0]
        if api.T.text(target_line, fmt="text-orig-full").strip():
            raise RuntimeError(
                f"{record_id}: the primary-only core format silently changed"
            )
        section = api.T.sectionFromNode(target_line)
        with webapp.test_client() as client:
            result = client.post(
                "/passage", data={"sec0": record_id, "sec1": str(section[1])}
            )
        payload = result.get_json()
        if result.status_code != 200 or not isinstance(payload, dict):
            raise RuntimeError(f"{record_id}: nonprimary browser route failed")
        html = payload.get("table")
        if not isinstance(html, str):
            raise RuntimeError(f"{record_id}: nonprimary browser HTML missing")
        extracted = VisibleText()
        extracted.feed(html)
        if source_snippet not in "".join(extracted.parts):
            raise RuntimeError(
                f"{record_id}: browser still hides {layer} content"
            )
    print("Pinned normalized-per-section browser: diplomatic and translation visible")

    # Source-critical reading: choose the textpart containing the actual
    # editorial node, not a guessed section index or a synthetic placeholder.
    for record_id, kind, expected in (
        ("abil0001", "gap", "gap"),
        ("abil0001", "supplied", "supplied"),
        ("abil0001", "unclear", "unclear"),
        ("caes0260", "abbr", "abbr"),
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
        if kind in {"supplied", "unclear", "abbr", "ex"}:
            closing_marker = f"⟦/{kind}⟧"
            if closing_marker not in "".join(visible_note.parts):
                raise RuntimeError(
                    f"{record_id}: native {kind} editorial end boundary invisible"
                )
        elif kind in {"gap", "glyph"} and f"⟦/{kind}⟧" in "".join(visible_note.parts):
            raise RuntimeError(
                f"{record_id}: a zero-width {kind} point was falsely given an end boundary"
            )
    # Brown bshe0146: an authored transcription <g ref=cross/> shares
    # its slot with a transcription_segmented <g/>. Both native markup
    # nodes must survive, but only authored evidence gets a browser badge.
    bshe = api.T.nodeFromSection(("bshe0146",))
    if bshe is None:
        raise RuntimeError("pinned bshe0146 source record missing")
    authored_glyphs = [
        m for m in api.L.d(bshe, otype="markup")
        if api.F.kind.v(m) == "glyph"
        and api.F.ref.v(m) == "cross"
        and api.F.annotation_source.v(m) != "transcription_segmented"
        and any(
            api.F.synthetic_kind.v(slot) == "glyph_ref"
            for slot in api.E.oslots.s(m)
        )
    ]
    if len(authored_glyphs) != 1:
        raise RuntimeError("bshe0146 authored reference not uniquely source-backed")
    native_slots = api.E.oslots.s(authored_glyphs[0])
    if len(native_slots) != 1:
        raise RuntimeError("bshe0146 expected one source glyph-reference slot")
    projected = [
        m for m in api.L.u(native_slots[0], otype="markup")
        if api.F.kind.v(m) == "glyph"
        and api.F.annotation_source.v(m) == "transcription_segmented"
    ]
    if len(projected) != 1:
        raise RuntimeError("bshe0146 projected segmented glyph disappeared")
    bshe_line = api.L.u(native_slots[0], otype="line")
    if len(bshe_line) != 1:
        raise RuntimeError("bshe0146 reference has no unique line")
    bshe_part = api.T.sectionFromNode(bshe_line[0])[1]
    with webapp.test_client() as client:
        displayed = client.post(
            "/passage", data={"sec0": "bshe0146", "sec1": str(bshe_part)}
        )
    html_data = displayed.get_json()
    if (
        displayed.status_code != 200
        or not isinstance(html_data, dict)
        or not isinstance(html_data.get("table"), str)
    ):
        raise RuntimeError("bshe0146 source glyph browser passage failed")
    native_text = VisibleText()
    native_text.feed(html_data["table"])
    content = "".join(native_text.parts)
    if content.count("⟦glyph ref=cross⟧") != 1 or "⟦glyph⟧" in content:
        raise RuntimeError("bshe0146 duplicate or missing source glyph badge")

    research_results = verify_pinned_examples(api)
    print(
        "Researcher examples verified: "
        + ", ".join(row["inscription_id"] for row in research_results["records"])
    )
    print("Pinned TF app: 5,535 sections; reference glyph preserved; HTTP / = 200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
