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
    if fmt in {"text-orig-full", "text-source-full"}:
        owners = tuple(api.L.u(node, otype="inscription"))
        if len(owners) != 1 or layer != api.F.primary_layer.v(owners[0]):
            return False
        allowed = {"both", "source"} if fmt == "text-source-full" else {"both", "normalized"}
        return role in allowed
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


def _sign_annotations(app: Any, node: int) -> list[str]:
    """Return visible notes at each *start* point, with no repeated spans."""
    api = app.api
    synthetic_feature = getattr(api.F, "synthetic_kind", None)
    synthetic = synthetic_feature.v(node) if synthetic_feature is not None else None
    point_kind = {"gap": "gap", "glyph_ref": "glyph"}.get(synthetic)
    emitted: set[int] = set()
    notes: list[str] = []
    for markup in api.L.u(node, otype="markup"):
        kind = api.F.kind.v(markup)
        if kind not in _RENDERED_MARKUP:
            continue
        if kind in {"gap", "glyph"}:
            if kind != point_kind:
                continue
        else:
            slots = api.E.oslots.s(markup)
            if not slots or slots[0] != node:
                continue
        if markup in emitted:
            continue
        emitted.add(markup)
        label = _annotation_label(app, markup)
        if label:
            notes.append(label)
    return notes


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
    original = app.api.T.text(node, fmt=fmt)
    material = escape("" if original is None else str(original))
    note_html = ""
    if _is_selected_sign(app, node, display_fmt):
        for label in _sign_annotations(app, node):
            note_html += (
                '<span class="iip-editorial-note" role="note">'
                f"⟦{escape(label)}⟧"
                "</span>"
            )
    return f'<span class="iip-source-sign">{material}</span>{note_html}'


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
