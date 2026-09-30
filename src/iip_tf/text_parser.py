"""Namespace-aware parser from IIP EpiDoc into the canonical textual IR."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from iip_tf.ir import (
    EdgeType,
    InscriptionIR,
    IREdge,
    IRNode,
    IRSign,
    Layer,
    NodeType,
    SourceIdentity,
    SourceProvenance,
)
from iip_tf.source_repair import SourceConflictError, repair_source_file

TEI_NS: Final = "http://www.tei-c.org/ns/1.0"
XML_NS: Final = "http://www.w3.org/XML/1998/namespace"
XML_ID: Final = f"{{{XML_NS}}}id"
XML_LANG: Final = f"{{{XML_NS}}}lang"

_NATIVE_LAYERS: Final = {
    ("edition", "transcription"): Layer.TRANSCRIPTION,
    ("edition", "diplomatic"): Layer.DIPLOMATIC,
    ("translation", None): Layer.TRANSLATION,
    ("commentary", None): Layer.COMMENTARY,
}

_MARKUP_KIND: Final = {
    "abbr": "abbr",
    "add": "add",
    "am": "am",
    "app": "apparatus",
    "cb": "column_break",
    "choice": "choice",
    "corr": "corr",
    "del": "del",
    "ex": "ex",
    "expan": "expan",
    "figure": "figure",
    "foreign": "foreign",
    "g": "glyph",
    "gap": "gap",
    "handShift": "hand_shift",
    "height": "height",
    "hi": "hi",
    "lb": "line_break",
    "lem": "lemma",
    "milestone": "milestone",
    "num": "num",
    "orig": "orig",
    "rdg": "reading",
    "reg": "reg",
    "sic": "sic",
    "space": "space",
    "subst": "subst",
    "supplied": "supplied",
    "surplus": "surplus",
    "unclear": "unclear",
}
_ENTITY_KIND: Final = {
    "date": "date",
    "name": "name",
    "persName": "person",
    "placeName": "place",
    "rs": "reference_string",
}
_ZERO_WIDTH_KIND: Final = {
    "cb": "column_break",
    "gap": "gap",
    "handShift": "hand_shift",
    "lb": "line_break",
    "milestone": "milestone",
    "space": "space",
    "figure": "figure",
}
_ROLE: Final = {
    "corr": "normalized",
    "reg": "normalized",
    "ex": "normalized",
    "supplied": "normalized",
    "sic": "source",
    "orig": "source",
    "am": "source",
    "del": "source",
    "surplus": "source",
}

_ALLOWED_ATTRS: Final[dict[str, frozenset[str]]] = {
    "div": frozenset({"ana", "change", "corresp", "n", "subtype", "type", "xml:id", "xml:lang"}),
    "p": frozenset({"cert", "xml:lang"}),
    "ab": frozenset(),
    "abbr": frozenset(),
    "add": frozenset({"place"}),
    "am": frozenset(),
    "app": frozenset({"type"}),
    "cb": frozenset(),
    "choice": frozenset(),
    "corr": frozenset(),
    "date": frozenset({"calendar", "from", "to"}),
    "del": frozenset({"extent", "quantity", "rend", "unit"}),
    "ex": frozenset({"cert"}),
    "expan": frozenset({"cert"}),
    "figDesc": frozenset(),
    "figure": frozenset(),
    "foreign": frozenset({"xml:lang"}),
    "g": frozenset({"cert", "ref", "type"}),
    "gap": frozenset(
        {"atLeast", "atMost", "cert", "extent", "precision", "quantity", "reason", "unit"}
    ),
    "handShift": frozenset({"cert", "new"}),
    "height": frozenset(),
    "hi": frozenset({"cert", "rend"}),
    "lb": frozenset({"break"}),
    "lem": frozenset(),
    "milestone": frozenset({"n", "unit"}),
    "name": frozenset({"type"}),
    "num": frozenset({"cert", "type", "value", "xml:id", "xml:lang"}),
    "orig": frozenset({"xml:id", "xml:lang"}),
    "persName": frozenset({"nymRef", "ref", "type", "xml:lang"}),
    "placeName": frozenset(),
    "rdg": frozenset(),
    "reg": frozenset(),
    "rs": frozenset({"ana", "type", "xml:lang"}),
    "sic": frozenset(),
    "space": frozenset({"dim", "extent", "quantity", "unit"}),
    "subst": frozenset(),
    "supplied": frozenset({"cert", "evidence", "extent", "reason", "unit"}),
    "surplus": frozenset({"cert"}),
    "unclear": frozenset({"cert", "reason"}),
    "w": frozenset({"xml:id", "xml:lang"}),
}

_ATTR_FEATURE: Final = {
    "ana": "source_ana",
    "change": "source_change",
    "corresp": "source_corresp",
    "n": "source_n",
    "subtype": "subtype",
    "type": "type",
    "cert": "cert",
    "place": "place",
    "extent": "extent",
    "quantity": "quantity",
    "rend": "rend",
    "unit": "unit",
    "calendar": "calendar",
    "from": "date_from",
    "to": "date_to",
    "atLeast": "at_least",
    "atMost": "at_most",
    "precision": "precision",
    "reason": "reason",
    "ref": "ref",
    "new": "new_hand",
    "break": "break",
    "value": "value",
    "nymRef": "nym_ref",
    "evidence": "evidence",
    "dim": "dim",
}

_ENTITY_ATTR_FEATURE: Final = {
    ("date", "calendar"): "calendar",
    ("date", "from"): "date_from",
    ("date", "to"): "date_to",
    ("name", "type"): "entity_type",
    ("persName", "nymRef"): "nym_ref",
    ("persName", "ref"): "ref",
    ("persName", "type"): "entity_type",
    ("rs", "ana"): "ana",
    ("rs", "type"): "entity_type",
}

_SUPPORTED_TEXTUAL_ELEMENTS: Final = frozenset(_ALLOWED_ATTRS)


class UnsupportedTextualConstructError(ValueError):
    """Raised when a textual source construct is outside frozen schema 0.1."""


@dataclass(frozen=True)
class TextDirectoryValidation:
    total_xml: int
    parsed: int
    skipped_test: int
    repaired: int
    failures: tuple[str, ...]


@dataclass
class _MutableSign:
    key: str
    glyph: str
    layer: Layer
    lang: str | None
    lang_source: str
    reading_role: str
    synthetic_kind: str | None
    after: str = ""


@dataclass(frozen=True)
class _Lang:
    value: str | None
    source: str


@dataclass
class _TextPartState:
    key: str
    layer: Layer
    line_start: int
    line_no: int = 1


def _local(name: str) -> str:
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def _attr_name(name: str) -> str:
    if name == XML_ID:
        return "xml:id"
    if name == XML_LANG:
        return "xml:lang"
    return _local(name)


def _clean_lang(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _child_lang(element: ET.Element, parent: _Lang) -> _Lang:
    explicit = _clean_lang(element.attrib.get(XML_LANG))
    if explicit is not None:
        return _Lang(explicit, "xml:lang")
    if parent.value is None:
        return _Lang(None, "none")
    if parent.source in {"xml:lang", "inherited"}:
        return _Lang(parent.value, "inherited")
    return parent


def _combine_role(parent: str, local: str) -> str:
    if local == "both":
        return parent
    if parent == "both":
        return local
    if parent == local:
        return parent
    return parent


def _paths(root: ET.Element) -> dict[int, str]:
    result: dict[int, str] = {}

    def visit(element: ET.Element, path: str) -> None:
        result[id(element)] = path
        counts: Counter[str] = Counter()
        for child in list(element):
            name = _local(child.tag)
            counts[name] += 1
            visit(child, f"{path}/{name}[{counts[name]}]")

    visit(root, f"/{_local(root.tag)}[1]")
    return result


class _Builder:
    def __init__(
        self,
        *,
        identity: SourceIdentity,
        provenance: SourceProvenance,
        paths: dict[int, str],
    ) -> None:
        self.identity = identity
        self.provenance = provenance
        self.paths = paths
        self.signs: list[_MutableSign] = []
        self.nodes: list[IRNode] = []
        self.edges: list[IREdge] = []
        self.seen_source_ids: set[str] = set()
        self.source_id_nodes: dict[str, str] = {}
        self.pending_corresp: list[tuple[str, str]] = []

    def source_key(self, element: ET.Element) -> str:
        source_id = element.attrib.get(XML_ID)
        if source_id:
            return f"{self.identity.inscription_id}#id:{source_id}"
        return f"{self.identity.inscription_id}#path:{self.paths[id(element)]}"

    def node_key(self, element: ET.Element) -> str:
        source_id = element.attrib.get(XML_ID)
        if source_id:
            if source_id in self.seen_source_ids:
                raise UnsupportedTextualConstructError(
                    f"{self.identity.source_file}: duplicate textual xml:id {source_id!r}"
                )
            self.seen_source_ids.add(source_id)
            return f"{self.identity.inscription_id}#id:{source_id}"
        return self.source_key(element)

    def derived_key(self, kind: str, suffix: str) -> str:
        return f"{self.identity.inscription_id}#derived:{kind}:{suffix}"

    def sign_keys(self, start: int, end: int | None = None) -> tuple[str, ...]:
        stop = len(self.signs) if end is None else end
        return tuple(sign.key for sign in self.signs[start:stop])

    def add_sign(
        self,
        *,
        glyph: str,
        layer: Layer,
        lang: _Lang,
        role: str,
        synthetic_kind: str | None = None,
    ) -> str:
        key = f"{self.identity.inscription_id}#s{len(self.signs) + 1}"
        self.signs.append(
            _MutableSign(
                key=key,
                glyph=glyph,
                layer=layer,
                lang=lang.value,
                lang_source=lang.source,
                reading_role=role,
                synthetic_kind=synthetic_kind,
            )
        )
        return key

    def add_space_after_last(self, layer: Layer) -> None:
        if not self.signs:
            return
        sign = self.signs[-1]
        if sign.layer == layer and sign.glyph and not sign.after:
            sign.after = " "

    def add_node(
        self,
        *,
        key: str,
        node_type: NodeType,
        start: int,
        end: int | None = None,
        features: dict[str, str | int] | None = None,
        source_id: str | None = None,
        parent: str | None = None,
    ) -> None:
        feature_items = tuple(sorted((features or {}).items()))
        node = IRNode(
            key=key,
            node_type=node_type,
            sign_keys=self.sign_keys(start, end),
            features=feature_items,
        )
        self.nodes.append(node)
        if source_id:
            self.source_id_nodes[source_id] = key
        if parent:
            self.edges.append(IREdge(EdgeType.PARENT, key, parent))
        corresp = (features or {}).get("source_corresp")
        if isinstance(corresp, str) and corresp:
            self.pending_corresp.append((key, corresp))

    def replace_parent(self, old: str, new: str) -> None:
        self.edges = [
            IREdge(edge.edge_type, edge.source, new)
            if edge.edge_type == EdgeType.PARENT and edge.target == old
            else edge
            for edge in self.edges
        ]

    def finalize_corresp(self) -> None:
        existing = {(edge.edge_type, edge.source, edge.target) for edge in self.edges}
        for source, raw in self.pending_corresp:
            for token in raw.split():
                if not token.startswith("#"):
                    continue
                target = self.source_id_nodes.get(token[1:])
                item = (EdgeType.CORRESPONDS_TO, source, target or "")
                if target and item not in existing:
                    self.edges.append(IREdge(EdgeType.CORRESPONDS_TO, source, target))
                    existing.add(item)

    def freeze(self) -> InscriptionIR:
        signs = tuple(
            IRSign(
                key=sign.key,
                glyph=sign.glyph,
                layer=sign.layer,
                lang=sign.lang,
                lang_source=sign.lang_source,
                reading_role=sign.reading_role,
                synthetic_kind=sign.synthetic_kind,
                after=sign.after,
            )
            for sign in self.signs
        )
        unique_edges = tuple(
            dict.fromkeys((edge.edge_type, edge.source, edge.target) for edge in self.edges)
        )
        edges = tuple(IREdge(*edge) for edge in unique_edges)
        return InscriptionIR(
            identity=self.identity,
            provenance=self.provenance,
            signs=signs,
            nodes=tuple(self.nodes),
            edges=edges,
            diagnostics=(),
        )


def _validate_attrs(element: ET.Element, *, source_file: str) -> None:
    name = _local(element.tag)
    allowed = _ALLOWED_ATTRS.get(name)
    if allowed is None:
        raise UnsupportedTextualConstructError(
            f"{source_file}: unsupported textual element {name!r}"
        )
    for raw_name in element.attrib:
        name_attr = _attr_name(raw_name)
        if name_attr not in allowed:
            raise UnsupportedTextualConstructError(
                f"{source_file}: unsupported textual attribute {name}@{name_attr}"
            )


def _mapped_features(
    element: ET.Element,
    *,
    layer: Layer,
    lang: _Lang,
    source_key: str,
    entity: bool = False,
) -> dict[str, str | int]:
    name = _local(element.tag)
    features: dict[str, str | int] = {
        "source_key": source_key,
        "layer": layer.value,
    }
    source_id = element.attrib.get(XML_ID)
    if source_id:
        features["source_id"] = source_id

    for raw_name, value in element.attrib.items():
        attr = _attr_name(raw_name)
        if attr == "xml:id":
            continue
        if attr == "xml:lang":
            features["lang"] = value.strip()
            features["lang_source"] = "xml:lang"
            continue
        if entity:
            mapped = _ENTITY_ATTR_FEATURE.get((name, attr))
        else:
            mapped = _ATTR_FEATURE.get(attr)
        if mapped:
            features[mapped] = value

    if lang.value is not None and "lang" not in features:
        features["lang"] = lang.value
        features["lang_source"] = lang.source
    return features


def _emit_text(
    builder: _Builder,
    text: str | None,
    *,
    layer: Layer,
    lang: _Lang,
    role: str,
) -> None:
    if not text:
        return
    if text.isspace():
        if "\n" not in text and "\r" not in text:
            builder.add_space_after_last(layer)
        return

    parts = re.split(r"(\s+)", text)
    for part in parts:
        if not part:
            continue
        if part.isspace():
            builder.add_space_after_last(layer)
            continue
        for char in part:
            builder.add_sign(glyph=char, layer=layer, lang=lang, role=role)


def _finish_line(builder: _Builder, state: _TextPartState) -> None:
    if len(builder.signs) <= state.line_start:
        return
    key = builder.derived_key("line", f"{state.key}:{state.line_no}")
    builder.add_node(
        key=key,
        node_type=NodeType.LINE,
        start=state.line_start,
        features={
            "line_n": state.line_no,
            "layer": state.layer.value,
        },
        parent=state.key,
    )
    state.line_no += 1
    state.line_start = len(builder.signs)


def _line_break(
    builder: _Builder,
    state: _TextPartState,
    *,
    lang: _Lang,
    role: str,
) -> tuple[int, int]:
    if len(builder.signs) > state.line_start:
        _finish_line(builder, state)
    start = len(builder.signs)
    builder.add_sign(
        glyph="",
        layer=state.layer,
        lang=lang,
        role=role,
        synthetic_kind="line_break",
    )
    return start, len(builder.signs)


def _parse_inline(
    builder: _Builder,
    element: ET.Element,
    *,
    layer: Layer,
    lang: _Lang,
    role: str,
    parent: str,
    state: _TextPartState,
) -> None:
    name = _local(element.tag)
    if name in {"p", "ab", "div", "w", "figDesc"}:
        raise UnsupportedTextualConstructError(
            f"{builder.identity.source_file}: unsupported inline element {name!r}"
        )
    _validate_attrs(element, source_file=builder.identity.source_file)
    child_lang = _child_lang(element, lang)
    local_role = _ROLE.get(name, "both")
    child_role = _combine_role(role, local_role)
    key = builder.node_key(element)
    source_id = element.attrib.get(XML_ID)
    start = len(builder.signs)

    if name == "lb":
        start, _ = _line_break(
            builder,
            state,
            lang=child_lang,
            role=child_role,
        )
    elif name in _ZERO_WIDTH_KIND:
        builder.add_sign(
            glyph="",
            layer=layer,
            lang=child_lang,
            role=child_role,
            synthetic_kind=_ZERO_WIDTH_KIND[name],
        )
    elif name == "g" and not (
        (element.text and element.text.strip()) or list(element)
    ):
        builder.add_sign(
            glyph="",
            layer=layer,
            lang=child_lang,
            role=child_role,
            synthetic_kind="glyph_ref",
        )
    elif name == "figure":
        builder.add_sign(
            glyph="",
            layer=layer,
            lang=child_lang,
            role=child_role,
            synthetic_kind="figure",
        )
    else:
        _emit_text(
            builder,
            element.text,
            layer=layer,
            lang=child_lang,
            role=child_role,
        )
        for child in list(element):
            child_name = _local(child.tag)
            if child_name == "figDesc":
                _validate_attrs(child, source_file=builder.identity.source_file)
            else:
                _parse_inline(
                    builder,
                    child,
                    layer=layer,
                    lang=child_lang,
                    role=child_role,
                    parent=key,
                    state=state,
                )
            _emit_text(
                builder,
                child.tail,
                layer=layer,
                lang=child_lang,
                role=child_role,
            )

    features = _mapped_features(
        element,
        layer=layer,
        lang=child_lang,
        source_key=builder.source_key(element),
        entity=name in _ENTITY_KIND,
    )
    if name in _ENTITY_KIND:
        features["entity_kind"] = _ENTITY_KIND[name]
        node_type = NodeType.ENTITY
    else:
        features["kind"] = _MARKUP_KIND[name]
        node_type = NodeType.MARKUP
        if name == "figure":
            descriptions = [
                "".join(child.itertext()).strip()
                for child in element
                if _local(child.tag) == "figDesc"
            ]
            description = " ".join(value for value in descriptions if value)
            if description:
                features["description"] = description

    builder.add_node(
        key=key,
        node_type=node_type,
        start=start,
        features=features,
        source_id=source_id,
        parent=parent,
    )


def _parse_paragraph(
    builder: _Builder,
    element: ET.Element,
    *,
    layer: Layer,
    lang: _Lang,
    parent: str,
    state: _TextPartState,
) -> None:
    name = _local(element.tag)
    if name not in {"p", "ab"}:
        raise UnsupportedTextualConstructError(
            f"{builder.identity.source_file}: expected paragraph, got {name!r}"
        )
    _validate_attrs(element, source_file=builder.identity.source_file)
    block_lang = _child_lang(element, lang)
    key = builder.node_key(element)
    start = len(builder.signs)

    _emit_text(builder, element.text, layer=layer, lang=block_lang, role="both")
    for child in list(element):
        _parse_inline(
            builder,
            child,
            layer=layer,
            lang=block_lang,
            role="both",
            parent=key,
            state=state,
        )
        _emit_text(
            builder,
            child.tail,
            layer=layer,
            lang=block_lang,
            role="both",
        )

    features = _mapped_features(
        element,
        layer=layer,
        lang=block_lang,
        source_key=builder.source_key(element),
    )
    features["kind"] = name
    builder.add_node(
        key=key,
        node_type=NodeType.PARAGRAPH,
        start=start,
        features=features,
        source_id=element.attrib.get(XML_ID),
        parent=parent,
    )


def _section_part(layer: Layer, element: ET.Element | None) -> str:
    if element is None:
        return layer.value
    parts = [layer.value]
    subtype = element.attrib.get("subtype")
    number = element.attrib.get("n")
    if subtype:
        parts.append(subtype)
    if number:
        parts.append(number)
    return ":".join(parts)


def _parse_textpart(
    builder: _Builder,
    element: ET.Element,
    *,
    layer: Layer,
    lang: _Lang,
    edition_key: str,
) -> None:
    _validate_attrs(element, source_file=builder.identity.source_file)
    if element.attrib.get("type") != "textpart":
        raise UnsupportedTextualConstructError(
            f"{builder.identity.source_file}: div inside edition is not type=textpart"
        )
    part_lang = _child_lang(element, lang)
    key = builder.node_key(element)
    start = len(builder.signs)
    state = _TextPartState(key=key, layer=layer, line_start=start)

    if element.text and element.text.strip():
        _emit_text(builder, element.text, layer=layer, lang=part_lang, role="both")
    for child in list(element):
        name = _local(child.tag)
        if name in {"p", "ab"}:
            _parse_paragraph(
                builder,
                child,
                layer=layer,
                lang=part_lang,
                parent=key,
                state=state,
            )
        else:
            _parse_inline(
                builder,
                child,
                layer=layer,
                lang=part_lang,
                role="both",
                parent=key,
                state=state,
            )
        _emit_text(builder, child.tail, layer=layer, lang=part_lang, role="both")

    _finish_line(builder, state)
    features = _mapped_features(
        element,
        layer=layer,
        lang=part_lang,
        source_key=builder.source_key(element),
    )
    features["section_part"] = _section_part(layer, element)
    builder.add_node(
        key=key,
        node_type=NodeType.TEXTPART,
        start=start,
        features=features,
        source_id=element.attrib.get(XML_ID),
        parent=edition_key,
    )


def _native_layer(element: ET.Element) -> Layer | None:
    if _local(element.tag) != "div":
        return None
    div_type = element.attrib.get("type")
    subtype = element.attrib.get("subtype")
    if div_type == "edition":
        return _NATIVE_LAYERS.get(("edition", subtype))
    return _NATIVE_LAYERS.get((div_type or "", None))


def _parse_edition(
    builder: _Builder,
    element: ET.Element,
    *,
    layer: Layer,
    header_lang: _Lang,
    inscription_key: str,
) -> None:
    _validate_attrs(element, source_file=builder.identity.source_file)
    edition_lang = _child_lang(element, header_lang)
    key = builder.node_key(element)
    source_id = element.attrib.get(XML_ID)
    start = len(builder.signs)
    children = list(element)
    explicit_parts = [
        child
        for child in children
        if _local(child.tag) == "div" and child.attrib.get("type") == "textpart"
    ]

    if explicit_parts:
        if element.text and element.text.strip():
            raise UnsupportedTextualConstructError(
                f"{builder.identity.source_file}: edition mixes explicit textparts "
                "with direct textual content"
            )
        for child in children:
            name = _local(child.tag)
            if child in explicit_parts:
                _parse_textpart(
                    builder,
                    child,
                    layer=layer,
                    lang=edition_lang,
                    edition_key=key,
                )
            else:
                raise UnsupportedTextualConstructError(
                    f"{builder.identity.source_file}: edition mixes explicit textparts "
                    f"with direct {name!r} content"
                )
            if child.tail and child.tail.strip():
                raise UnsupportedTextualConstructError(
                    f"{builder.identity.source_file}: edition has direct text outside "
                    "explicit textparts"
                )
    else:
        implicit_key = builder.derived_key("textpart", f"{key}:implicit")
        implicit_start = len(builder.signs)
        implicit_state = _TextPartState(
            key=implicit_key,
            layer=layer,
            line_start=implicit_start,
        )
        implicit_child_keys_before = len(builder.edges)

        _emit_text(builder, element.text, layer=layer, lang=edition_lang, role="both")
        for child in children:
            name = _local(child.tag)
            if name in {"p", "ab"}:
                _parse_paragraph(
                    builder,
                    child,
                    layer=layer,
                    lang=edition_lang,
                    parent=implicit_key,
                    state=implicit_state,
                )
            elif name == "div":
                raise UnsupportedTextualConstructError(
                    f"{builder.identity.source_file}: unsupported nested div "
                    f"type={child.attrib.get('type')!r}"
                )
            else:
                _parse_inline(
                    builder,
                    child,
                    layer=layer,
                    lang=edition_lang,
                    role="both",
                    parent=implicit_key,
                    state=implicit_state,
                )
            _emit_text(builder, child.tail, layer=layer, lang=edition_lang, role="both")

        implicit_end = len(builder.signs)
        if implicit_end > implicit_start:
            _finish_line(builder, implicit_state)
            builder.add_node(
                key=implicit_key,
                node_type=NodeType.TEXTPART,
                start=implicit_start,
                end=implicit_end,
                features={
                    "source_key": implicit_key,
                    "layer": layer.value,
                    "section_part": _section_part(layer, None),
                },
                parent=key,
            )
        elif len(builder.edges) > implicit_child_keys_before:
            builder.replace_parent(implicit_key, key)

    features = _mapped_features(
        element,
        layer=layer,
        lang=edition_lang,
        source_key=builder.source_key(element),
    )
    features["edition_kind"] = layer.value
    features["empty"] = "1" if len(builder.signs) == start else "0"
    builder.add_node(
        key=key,
        node_type=NodeType.EDITION,
        start=start,
        features=features,
        source_id=source_id,
        parent=inscription_key,
    )

def _identity(root: ET.Element, path: Path) -> SourceIdentity:
    inscription_id = path.stem
    xml_id = root.attrib.get(XML_ID)
    iip_ids = tuple(
        value
        for element in root.iter()
        if _local(element.tag) == "idno"
        and element.attrib.get("type") == "IIP"
        and (value := "".join(element.itertext()).strip())
    )
    text_lang = next(
        (element for element in root.iter() if _local(element.tag) == "textLang"),
        None,
    )
    main_lang = _clean_lang(text_lang.attrib.get("mainLang")) if text_lang is not None else None
    return SourceIdentity(
        inscription_id=inscription_id,
        source_file=path.name,
        xml_id=xml_id,
        iip_ids=iip_ids,
        main_lang=main_lang,
    )


def parse_epidoc_file(path: Path, *, source_revision: str) -> InscriptionIR:
    """Parse one repaired/validated IIP record into the canonical textual IR."""

    repaired = repair_source_file(path, source_revision=source_revision)
    try:
        root = ET.fromstring(repaired.text)
    except ET.ParseError as exc:  # defensive: source_repair already validates
        raise SourceConflictError(f"{path.name}: malformed XML after preflight: {exc}") from exc

    if _local(root.tag) != "TEI":
        raise UnsupportedTextualConstructError(f"{path.name}: root is not TEI")

    identity = _identity(root, path)
    provenance = SourceProvenance(
        source_revision=source_revision,
        repaired=repaired.repaired,
        repair_id=repaired.repair_id,
        conflict_count=repaired.conflict_count,
    )
    builder = _Builder(identity=identity, provenance=provenance, paths=_paths(root))
    inscription_key = builder.derived_key("record", identity.inscription_id)
    header_lang = _Lang(identity.main_lang, "textLang.mainLang" if identity.main_lang else "none")

    native_editions: list[tuple[ET.Element, Layer]] = []
    for element in root.iter():
        layer = _native_layer(element)
        if layer is not None:
            native_editions.append((element, layer))

    layer_starts: dict[Layer, int] = {}
    layer_ends: dict[Layer, int] = {}
    for element, layer in native_editions:
        layer_starts.setdefault(layer, len(builder.signs))
        _parse_edition(
            builder,
            element,
            layer=layer,
            header_lang=header_lang,
            inscription_key=inscription_key,
        )
        layer_ends[layer] = len(builder.signs)

    transcription_has = layer_ends.get(Layer.TRANSCRIPTION, 0) > layer_starts.get(
        Layer.TRANSCRIPTION, layer_ends.get(Layer.TRANSCRIPTION, 0)
    )
    diplomatic_has = layer_ends.get(Layer.DIPLOMATIC, 0) > layer_starts.get(
        Layer.DIPLOMATIC, layer_ends.get(Layer.DIPLOMATIC, 0)
    )
    if transcription_has:
        primary_layer = "transcription"
    elif diplomatic_has:
        primary_layer = "diplomatic"
    else:
        primary_layer = "empty"
        builder.add_sign(
            glyph="",
            layer=Layer.ANCHOR,
            lang=_Lang(None, "none"),
            role="both",
            synthetic_kind="anchor",
        )

    inscription_features: dict[str, str | int] = {
        "inscription_id": identity.inscription_id,
        "source_file": identity.source_file,
        "primary_layer": primary_layer,
    }
    if identity.xml_id:
        inscription_features["xml_id"] = identity.xml_id
    if identity.iip_ids:
        inscription_features["iip_id"] = identity.iip_ids[0]
    if identity.main_lang:
        inscription_features["main_lang"] = identity.main_lang

    builder.add_node(
        key=inscription_key,
        node_type=NodeType.INSCRIPTION,
        start=0,
        features=inscription_features,
    )
    builder.finalize_corresp()
    return builder.freeze()


def validate_text_directory(
    source_dir: Path,
    *,
    source_revision: str,
) -> TextDirectoryValidation:
    """Parse all non-test top-level XML files and report deterministic failures."""

    paths = sorted(source_dir.glob("*.xml"))
    parsed = 0
    repaired_count = 0
    skipped = 0
    failures: list[str] = []
    for path in paths:
        if "test" in path.name.lower():
            skipped += 1
            continue
        try:
            ir = parse_epidoc_file(path, source_revision=source_revision)
        except (SourceConflictError, UnsupportedTextualConstructError, ValueError) as exc:
            failures.append(f"{path.name}: {exc}")
            continue
        parsed += 1
        if ir.provenance.repaired:
            repaired_count += 1

    return TextDirectoryValidation(
        total_xml=len(paths),
        parsed=parsed,
        skipped_test=skipped,
        repaired=repaired_count,
        failures=tuple(failures),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m iip_tf.text_parser",
        description="Validate native textual EpiDoc against the frozen IIP-TF IR contract.",
    )
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expect-parsed", type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_text_directory(args.source_dir, source_revision=args.revision)
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))
    if report.failures:
        return 1
    if args.expect_parsed is not None and report.parsed != args.expect_parsed:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
