"""Source-critical display annotations for the standard Text-Fabric browser.

All actual characters still come from native TF's currently requested text
format. Editorial notes are visual labels, never changes to source reading.
"""

from __future__ import annotations

import types
from html import escape
from typing import Any

from tf.advanced.app import App

_ANNOTATION_FEATURES = {
    "supplied": ("reason", "cert"),
    "unclear": ("cert",),
    "abbr": ("cert",),
    "ex": ("cert",),
    "gap": ("reason", "extent", "unit", "quantity", "cert"),
    "glyph": ("ref", "cert"),
}
_RENDERED_MARKUP = frozenset(_ANNOTATION_FEATURES)


def _is_selected_sign(app: Any, node: int, fmt: str | None) -> bool:
    """Prevent a nonprimary layer's apparatus from leaking into primary text."""
    api = app.api
    layer = api.F.layer.v(node)
    role = api.F.reading_role.v(node)
    layer_for_format = {
        "text-transcription-full": "transcription",
        "text-diplomatic-full": "diplomatic",
        "text-translation-full": "translation",
        "text-commentary-full": "commentary",
    }
    if fmt in {"text-orig-full", "text-orig-refs-full", "text-source-full"}:
        owners = tuple(api.L.u(node, otype="inscription"))
        if len(owners) != 1 or layer != api.F.primary_layer.v(owners[0]):
            return False
        allowed = {"both", "source"} if fmt == "text-source-full" else {"both", "normalized"}
        return role in allowed
    if fmt == "text-section-normalized-full":
        return layer in layer_for_format.values() and role in {"both", "normalized"}
    if fmt in layer_for_format:
        return layer == layer_for_format[fmt] and role in {"both", "normalized"}
    if fmt == "text-layer-full":
        return True
    # Unknown TF text formats are rendered verbatim, without guessed
    # primary-source apparatus overlays.
    return False


def _annotation_label(app: Any, markup: int) -> str:
    """Escape native TF feature values; never insert raw EpiDoc into HTML."""
    F = app.api.F
    kind = F.kind.v(markup)
    if kind not in _RENDERED_MARKUP:
        return ""
    pieces = [kind]
    for feature in _ANNOTATION_FEATURES[kind]:
        fapi = getattr(F, feature, None)
        value = fapi.v(markup) if fapi is not None else None
        if value not in (None, ""):
            pieces.append(f"{feature}={value}")
    return " ".join(pieces)


_SPAN_KINDS = frozenset({"supplied", "unclear", "abbr", "ex"})
# Native otext composes these features after the actual glyph/ref token.
# A source-tail space may attach to the sign BEFORE an editor's end boundary;
# the boundary must precede that space while retaining its exact bytes.
_AFTER_FEATURE = {
    "text-orig-full": "primary_after",
    "text-orig-refs-full": "primary_after",
    "text-layer-full": "after",
    "text-source-full": "source_after",
    "text-transcription-full": "transcription_after",
    "text-diplomatic-full": "diplomatic_after",
    "text-translation-full": "translation_after",
    "text-commentary-full": "commentary_after",
}


def _markup_depth(app: Any, markup: int) -> int:
    """Native parent edges decide ordering for equal-slot nested scopes."""
    api = app.api
    parent_api = getattr(api.E, "parent", None)
    if parent_api is None:
        return 0
    seen = {markup}
    frontier = {markup}
    depth = 0
    while frontier and depth < 64:
        next_frontier: set[int] = set()
        for node in frontier:
            for parent in parent_api.f(node):
                if parent not in seen and api.F.otype.v(parent) == "markup":
                    next_frontier.add(parent)
        if not next_frontier:
            break
        depth += 1
        seen.update(next_frontier)
        frontier = next_frontier
    return depth


def _eligible_slots(app: Any, markup: int, fmt: str | None) -> tuple[int, ...]:
    """Keep boundaries on the actually selected reading, not hidden variants."""
    slots: tuple[int, ...] = tuple(app.api.E.oslots.s(markup))
    if fmt is None:
        return slots
    return tuple(s for s in slots if _is_selected_sign(app, s, fmt))


def _is_source_markup(app: Any, markup: int) -> bool:
    """Do not display a projected segmented glyph as authored source evidence."""
    api = app.api
    kind = api.F.kind.v(markup)
    annotation_source = getattr(api.F, "annotation_source", None)
    return not (
        kind == "glyph"
        and annotation_source is not None
        and annotation_source.v(markup) == "transcription_segmented"
    )


def _sign_annotations(
    app: Any, node: int, fmt: str | None = None
) -> list[str]:
    """Opening labels precede first *visible* sign; source gaps stay points."""
    api = app.api
    synthetic_feature = getattr(api.F, "synthetic_kind", None)
    synthetic = synthetic_feature.v(node) if synthetic_feature is not None else None
    point_kind = {"gap": "gap", "glyph_ref": "glyph"}.get(synthetic)
    candidates: list[tuple[int, int, int, str]] = []
    for markup in api.L.u(node, otype="markup"):
        kind = api.F.kind.v(markup)
        if kind not in _RENDERED_MARKUP or not _is_source_markup(app, markup):
            continue
        slots = _eligible_slots(app, markup, fmt)
        if not slots or slots[0] != node:
            continue
        if kind in {"gap", "glyph"} and kind != point_kind:
            continue
        label = _annotation_label(app, markup)
        if label:
            # Longer/outer scopes open before shorter/inner scopes.
            candidates.append((_markup_depth(app, markup), -len(slots), markup, label))
    return [entry[3] for entry in sorted(candidates)]


def _end_annotations(app: Any, node: int, fmt: str) -> list[str]:
    """Close a true source span after its last visible sign, inner first.

    Zero-width source events have no span boundary and are never closed.
    """
    api = app.api
    candidates: list[tuple[int, int, int, str]] = []
    for markup in api.L.u(node, otype="markup"):
        kind = api.F.kind.v(markup)
        if kind not in _SPAN_KINDS:
            continue
        slots = _eligible_slots(app, markup, fmt)
        if not slots or slots[-1] != node:
            continue
        # Deeper/shorter nested source spans close before their outer scope.
        candidates.append((-_markup_depth(app, markup), len(slots), markup, kind))
    return [entry[3] for entry in sorted(candidates)]


def render_sign(app: Any, options: Any, chunk: Any, n_type: str, outer: bool) -> str:
    """Render one sign without suppressing its original characters or spacing."""
    node = chunk[0]
    fmt = getattr(options, "fmt", None)
    # The standard TF browser and app.plain() may pass fmt=None while
    # displaying context.textFormat. Do not mistake that for an unknown
    # corpus layer, or the annotation overlay silently disappears.
    display_fmt = fmt or getattr(app.context, "textFormat", None)
    if display_fmt is None:
        display_fmt = app.api.T.defaultFormat
    # The app may select a non-corpus-default format while options.fmt=None.
    # Use the SAME effective format for text and source-critical badges.
    original = app.api.T.text(node, fmt=display_fmt)
    material = escape("" if original is None else str(original))
    note_html = ""
    if _is_selected_sign(app, node, display_fmt):
        for label in _sign_annotations(app, node, display_fmt):
            note_html += (
                '<span class="iip-editorial-note" role="note">'
                f"⟦{escape(label)}⟧"
                "</span>"
            )
        ends = "".join(
            '<span class="iip-editorial-note iip-editorial-end" role="note" '
            f'aria-label="End of {escape(kind)}">⟦/{escape(kind)}⟧</span>'
            for kind in _end_annotations(app, node, display_fmt)
        )
    else:
        ends = ""
    # EpiDoc tail whitespace *after* </supplied> is often stored as the
    # preceding sign's native `after` feature. Close the editorial span
    # after the actual sign, but BEFORE that following whitespace.
    after_html = ""
    if ends:
        after_feature_name = (
            f"{layer}_after" if display_fmt == "text-section-normalized-full"
            and (layer := app.api.F.layer.v(node)) in {
                "transcription", "diplomatic", "translation", "commentary"
            }
            else _AFTER_FEATURE.get(display_fmt)
        )
        after_feature = (
            getattr(app.api.F, after_feature_name, None)
            if after_feature_name is not None else None
        )
        after_value = after_feature.v(node) if after_feature is not None else None
        if isinstance(after_value, str) and after_value and str(original).endswith(after_value):
            material = escape(str(original)[:-len(after_value)])
            after_html = f'<span class="iip-source-sign">{escape(after_value)}</span>'
    # All native reading bytes remain in order, even when an end boundary
    # falls between a glyph/ref token and its source-tail whitespace.
    return f'{note_html}<span class="iip-source-sign">{material}</span>{ends}{after_html}'


def install_editorial_renderer(app: Any) -> None:
    """Register one sign-only renderer in TF's existing method registry."""
    custom = getattr(app, "customMethods", None)
    plain = getattr(custom, "plainCustom", None) if custom is not None else None
    if plain is None or app.api is None:
        return
    plain["sign"] = types.MethodType(render_sign, app)


class TfApp(App):
    """IIP-TF app with native, unambiguous source-critical display notes."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        install_editorial_renderer(self)

    def reinit(self) -> None:
        install_editorial_renderer(self)
