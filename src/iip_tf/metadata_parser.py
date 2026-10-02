"""Parse schema-0.1 IIP metadata into the canonical IR."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import replace
from typing import Final

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode, NodeType

TEI_NS: Final = "http://www.tei-c.org/ns/1.0"
XML_NS: Final = "http://www.w3.org/XML/1998/namespace"
XML_ID: Final = f"{{{XML_NS}}}id"
XML_LANG: Final = f"{{{XML_NS}}}lang"
_NS: Final = {"tei": TEI_NS}

_METADATA_ATTRS: Final[dict[str, frozenset[str]]] = {
    "textLang": frozenset({"mainLang", "otherLangs"}),
    "msItem": frozenset({"ana", "cert", "class"}),
    "objectDesc": frozenset({"ana"}),
    "supportDesc": frozenset({"ana"}),
    "support": frozenset({"ana"}),
    "condition": frozenset({"ana"}),
    "layout": frozenset({"columns", "writtenLines"}),
    "layoutDesc": frozenset(),
    "handDesc": frozenset(),
    "decoDesc": frozenset(),
    "origin": frozenset(),
    "placeName": frozenset(),
    "geo": frozenset(),
    "lb": frozenset({"break"}),
    "div": frozenset({"type"}),
    "listBibl": frozenset(),
    "dimensions": frozenset({"atLeast", "atMost", "extent", "quantity", "type", "unit"}),
    "height": frozenset({"atLeast", "atMost"}),
    "width": frozenset({"atLeast", "atMost"}),
    "depth": frozenset({"atLeast", "atMost"}),
    "date": frozenset({"notAfter", "notBefore", "period", "precision"}),
    "region": frozenset({"cert"}),
    "settlement": frozenset({"cert", "ref"}),
    "geogName": frozenset({"type"}),
    "geogFeat": frozenset({"type"}),
    "bibl": frozenset({"xml:id"}),
    "ptr": frozenset({"target", "type"}),
    "biblScope": frozenset({"n", "unit", "xml:id"}),
    "handNote": frozenset({"ana", "xml:id"}),
    "decoNote": frozenset({"ana", "xml:id"}),
    "facsimile": frozenset(),
    "surface": frozenset({"xml:id"}),
    "desc": frozenset(),
    "graphic": frozenset({"url", "xml:id"}),
    "persName": frozenset({"role"}),
    "note": frozenset(),
    "revisionDesc": frozenset(),
    "change": frozenset({"when", "when-custom", "who", "xml:id"}),
    "p": frozenset(),
    "foreign": frozenset(),
    "ab": frozenset(),
    "locus": frozenset(),
}


class MetadataParseError(ValueError):
    """Raised when mapped metadata cannot be represented losslessly."""


def _local(name: str) -> str:
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def _metadata_element_name(name: str) -> str:
    if not name.startswith("{"):
        raise MetadataParseError(
            f"{name}: unresearched namespace {''!r}"
        )
    namespace, local = name[1:].split("}", 1)
    if namespace != TEI_NS:
        raise MetadataParseError(
            f"{local}: unresearched namespace {namespace!r}"
        )
    return local


def _attr_name(name: str) -> str:
    if name == XML_ID:
        return "xml:id"
    if name == XML_LANG:
        return "xml:lang"
    if name.startswith("{"):
        namespace, local = name[1:].split("}", 1)
        if namespace == XML_NS:
            return f"xml:{local}"
        raise MetadataParseError(
            f"{local}: unresearched namespace {namespace!r}"
        )
    return name


def _validate_attrs(element: ET.Element) -> None:
    name = _metadata_element_name(element.tag)
    allowed = _METADATA_ATTRS.get(name)
    if allowed is None:
        raise MetadataParseError(f"unsupported mapped metadata element {name!r}")
    for raw_name in element.attrib:
        attr = _attr_name(raw_name)
        if attr not in allowed:
            raise MetadataParseError(f"{name}@{attr}: unsupported mapped metadata attribute")


def _validate_children(element: ET.Element, allowed: set[str]) -> None:
    name = _metadata_element_name(element.tag)
    child_names = [
        _metadata_element_name(child.tag)
        for child in list(element)
    ]
    unknown = [
        child_name
        for child_name in child_names
        if child_name not in allowed
    ]
    if unknown:
        raise MetadataParseError(
            f"{name}: unsupported mapped metadata children {unknown!r}"
        )


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = " ".join("".join(element.itertext()).split())
    return value or None


def _metadata_text(
    element: ET.Element,
    *,
    allowed_children: set[str] | None = None,
) -> str | None:
    _validate_attrs(element)
    allowed = set() if allowed_children is None else allowed_children
    _validate_children(element, allowed)
    for child in list(element):
        _validate_attrs(child)
        _validate_children(child, set())
    return _text(element)


def _direct_text(element: ET.Element) -> str | None:
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in list(element):
        if child.tail:
            parts.append(child.tail)
    value = " ".join("".join(parts).split())
    return value or None


def _values(elements: list[ET.Element], attr: str | None = None) -> list[str]:
    values: list[str] = []
    for element in elements:
        raw = element.attrib.get(attr) if attr is not None else _text(element)
        if raw is None:
            continue
        value = raw.strip()
        if value:
            values.append(value)
    return values


def _scalar(name: str, values: list[str]) -> str | None:
    distinct = list(dict.fromkeys(values))
    if len(distinct) > 1:
        raise MetadataParseError(
            f"{name}: multiple distinct scalar values {distinct!r}"
        )
    return distinct[0] if distinct else None


def _int_derivative(value: str | None) -> int | None:
    if value is None or re.fullmatch(r"[+-]?\d+", value) is None:
        return None
    return int(value)


def _paths(root: ET.Element) -> dict[int, str]:
    paths: dict[int, str] = {}

    def visit(element: ET.Element, path: str) -> None:
        paths[id(element)] = path
        counts: Counter[str] = Counter()
        for child in list(element):
            name = _local(child.tag)
            counts[name] += 1
            visit(child, f"{path}/{name}[{counts[name]}]")

    visit(root, f"/{_local(root.tag)}[1]")
    return paths


def _source_key(
    element: ET.Element,
    *,
    inscription_id: str,
    paths: dict[int, str],
) -> str:
    source_id = element.attrib.get(XML_ID)
    if source_id:
        return f"{inscription_id}#id:{source_id}"
    return f"{inscription_id}#path:{paths[id(element)]}"


def _anchor(ir: InscriptionIR) -> str:
    inscription = ir.nodes_of_type(NodeType.INSCRIPTION)
    if len(inscription) != 1:
        raise MetadataParseError(
            f"expected one inscription node, found {len(inscription)}"
        )
    primary = inscription[0].feature("primary_layer")
    if isinstance(primary, str) and primary != "empty":
        for sign in ir.signs:
            if sign.layer.value == primary:
                return sign.key
    for sign in ir.signs:
        if sign.synthetic_kind == "anchor":
            return sign.key
    if ir.signs:
        return ir.signs[0].key
    raise MetadataParseError("record has no sign available for metadata anchoring")


def _append_feature(
    features: dict[str, str | int],
    name: str,
    value: str | int | None,
) -> None:
    if value is not None and value != "":
        features[name] = value


def _dimension_features(
    element: ET.Element,
    *,
    source_key: str,
) -> dict[str, str | int]:
    _validate_attrs(element)
    features: dict[str, str | int] = {"source_key": source_key}
    mapping = {
        "type": "dimension_type",
        "extent": "dimension_extent",
        "unit": "dimension_unit",
        "quantity": "quantity",
        "atLeast": "at_least",
        "atMost": "at_most",
    }
    for attr, feature in mapping.items():
        _append_feature(features, feature, element.attrib.get(attr))

    for child in list(element):
        name = _local(child.tag)
        if name not in {"height", "width", "depth"}:
            raise MetadataParseError(
                f"dimensions: unsupported child {name!r}"
            )
        _validate_attrs(child)
        _append_feature(features, name, _metadata_text(child))
        _append_feature(features, f"{name}_min", child.attrib.get("atLeast"))
        _append_feature(features, f"{name}_max", child.attrib.get("atMost"))
    return features


def _make_node(
    *,
    key: str,
    node_type: NodeType,
    anchor: str,
    features: dict[str, str | int],
) -> IRNode:
    return IRNode(
        key=key,
        node_type=node_type,
        sign_keys=(anchor,),
        features=tuple(sorted(features.items())),
    )


def _add_owned(
    *,
    nodes: list[IRNode],
    edges: list[IREdge],
    node: IRNode,
    inscription_key: str,
    parent: str | None = None,
) -> None:
    nodes.append(node)
    edges.append(IREdge(EdgeType.IN_INSCRIPTION, node.key, inscription_key))
    edges.append(
        IREdge(
            EdgeType.PARENT,
            node.key,
            inscription_key if parent is None else parent,
        )
    )


def _scalar_metadata(root: ET.Element) -> dict[str, str | int]:
    features: dict[str, str | int] = {}

    text_langs = root.findall(".//tei:msContents/tei:textLang", _NS)
    for element in text_langs:
        _validate_attrs(element)
    _append_feature(
        features,
        "main_lang",
        _scalar("main_lang", _values(text_langs, "mainLang")),
    )
    _append_feature(
        features,
        "other_langs",
        _scalar("other_langs", _values(text_langs, "otherLangs")),
    )

    ms_items = root.findall(".//tei:msContents/tei:msItem", _NS)
    for element in ms_items:
        _validate_attrs(element)
        _validate_children(element, {"p"})
    _append_feature(features, "genre", _scalar("genre", _values(ms_items, "class")))
    _append_feature(
        features,
        "genre_cert",
        _scalar("genre_cert", _values(ms_items, "cert")),
    )
    _append_feature(
        features,
        "religion",
        _scalar("religion", _values(ms_items, "ana")),
    )

    object_descs = root.findall(".//tei:physDesc/tei:objectDesc", _NS)
    for element in object_descs:
        _validate_attrs(element)
        _validate_children(element, {"supportDesc", "layoutDesc"})
    _append_feature(
        features,
        "object_type",
        _scalar("object_type", _values(object_descs, "ana")),
    )

    support_descs = root.findall(".//tei:objectDesc/tei:supportDesc", _NS)
    supports = root.findall(".//tei:objectDesc/tei:supportDesc/tei:support", _NS)
    for element in support_descs:
        _validate_attrs(element)
        _validate_children(element, {"support", "condition"})
    for element in supports:
        _validate_attrs(element)
        _validate_children(element, {"p", "dimensions"})
    _append_feature(
        features,
        "material",
        _scalar(
            "material",
            [*_values(support_descs, "ana"), *_values(supports, "ana")],
        ),
    )
    conditions = root.findall(".//tei:supportDesc/tei:condition", _NS)
    for element in conditions:
        _validate_attrs(element)
        _validate_children(element, {"p"})
    _append_feature(
        features,
        "condition",
        _scalar("condition", _values(conditions, "ana")),
    )
    condition_notes = [
        child
        for condition in conditions
        for child in list(condition)
        if _local(child.tag) == "p"
    ]
    _append_feature(
        features,
        "condition_note",
        _scalar(
            "condition_note",
            [
                value
                for element in condition_notes
                if (value := _metadata_text(element))
            ],
        ),
    )

    layout_descs = root.findall(".//tei:objectDesc/tei:layoutDesc", _NS)
    for element in layout_descs:
        _validate_attrs(element)
        _validate_children(element, {"layout"})
    layouts = root.findall(".//tei:objectDesc/tei:layoutDesc/tei:layout", _NS)
    for element in layouts:
        _validate_attrs(element)
        _validate_children(element, {"p"})
    _append_feature(
        features,
        "layout_columns",
        _scalar("layout_columns", _values(layouts, "columns")),
    )
    _append_feature(
        features,
        "layout_written_lines",
        _scalar("layout_written_lines", _values(layouts, "writtenLines")),
    )
    layout_notes = [
        child
        for layout in layouts
        for child in list(layout)
        if _local(child.tag) == "p"
    ]
    _append_feature(
        features,
        "layout_note",
        _scalar(
            "layout_note",
            [
                value
                for element in layout_notes
                if (value := _metadata_text(element))
            ],
        ),
    )

    origins = root.findall(".//tei:history/tei:origin", _NS)
    for element in origins:
        _validate_attrs(element)
        _validate_children(element, {"date", "placeName", "p"})
    origin_dates = [
        child
        for origin in origins
        for child in list(origin)
        if _local(child.tag) == "date"
    ]
    for element in origin_dates:
        _validate_attrs(element)
    date_before = _scalar("date_not_before", _values(origin_dates, "notBefore"))
    date_after = _scalar("date_not_after", _values(origin_dates, "notAfter"))
    _append_feature(features, "date_not_before", date_before)
    _append_feature(features, "date_not_after", date_after)
    _append_feature(
        features, "date_not_before_int", _int_derivative(date_before)
    )
    _append_feature(features, "date_not_after_int", _int_derivative(date_after))
    _append_feature(
        features,
        "date_text",
        _scalar(
            "date_text",
            [value for e in origin_dates if (value := _metadata_text(e))],
        ),
    )
    _append_feature(
        features,
        "date_precision",
        _scalar("date_precision", _values(origin_dates, "precision")),
    )
    _append_feature(
        features,
        "period_ref",
        _scalar("period_ref", _values(origin_dates, "period")),
    )

    origin_places = [
        child
        for origin in origins
        for child in list(origin)
        if _local(child.tag) == "placeName"
    ]
    for place in origin_places:
        _validate_attrs(place)
        _validate_children(
            place,
            {"region", "settlement", "geogName", "geogFeat", "geo", "lb"},
        )
        for child in list(place):
            if _local(child.tag) == "lb":
                _validate_attrs(child)

    regions = [
        child
        for place in origin_places
        for child in list(place)
        if _local(child.tag) == "region"
    ]
    settlements = [
        child
        for place in origin_places
        for child in list(place)
        if _local(child.tag) == "settlement"
    ]
    geog_names = [
        child
        for place in origin_places
        for child in list(place)
        if _local(child.tag) == "geogName"
    ]
    geog_feats = [
        child
        for place in origin_places
        for child in list(place)
        if _local(child.tag) == "geogFeat"
    ]
    geos = [
        geo
        for place in origin_places
        for geo in place.findall(".//tei:geo", _NS)
    ]

    for element in regions:
        _validate_attrs(element)
    for element in settlements:
        _validate_attrs(element)
        _validate_children(element, {"geo"})
    for element in geog_names:
        _validate_attrs(element)
        if element.attrib.get("type") not in {None, "site"}:
            raise MetadataParseError(
                f"geogName@type: unsupported mapped value {element.attrib.get('type')!r}"
            )
    for element in geog_feats:
        _validate_attrs(element)
        if element.attrib.get("type") not in {None, "locus"}:
            raise MetadataParseError(
                f"geogFeat@type: unsupported mapped value {element.attrib.get('type')!r}"
            )

    _append_feature(
        features,
        "region",
        _scalar(
            "region",
            [value for e in regions if (value := _metadata_text(e))],
        ),
    )
    _append_feature(
        features,
        "region_cert",
        _scalar("region_cert", _values(regions, "cert")),
    )
    _append_feature(
        features,
        "settlement",
        _scalar(
            "settlement",
            [value for e in settlements if (value := _direct_text(e))],
        ),
    )
    _append_feature(
        features,
        "settlement_cert",
        _scalar("settlement_cert", _values(settlements, "cert")),
    )
    _append_feature(
        features,
        "settlement_ref",
        _scalar("settlement_ref", _values(settlements, "ref")),
    )
    _append_feature(
        features,
        "site",
        _scalar(
            "site",
            [value for e in geog_names if (value := _metadata_text(e))],
        ),
    )
    _append_feature(
        features,
        "locus",
        _scalar(
            "locus",
            [value for e in geog_feats if (value := _metadata_text(e))],
        ),
    )
    _append_feature(
        features,
        "geo",
        _scalar(
            "geo",
            [value for e in geos if (value := _metadata_text(e))],
        ),
    )
    origin_notes = [
        child
        for origin in origins
        for child in list(origin)
        if _local(child.tag) == "p"
    ]
    _append_feature(
        features,
        "origin_note",
        _scalar(
            "origin_note",
            [
                value
                for element in origin_notes
                if (value := _metadata_text(element))
            ],
        ),
    )

    provenance_places = root.findall(
        ".//tei:history/tei:provenance/tei:placeName", _NS
    )
    _append_feature(
        features,
        "provenance_place",
        _scalar(
            "provenance_place",
            [
                value
                for element in provenance_places
                if (value := _metadata_text(element))
            ],
        ),
    )
    return features


def enrich_metadata(ir: InscriptionIR, root: ET.Element) -> InscriptionIR:
    """Return a new IR with schema-0.1 header/facsimile metadata."""

    paths = _paths(root)
    anchor = _anchor(ir)
    inscription_nodes = ir.nodes_of_type(NodeType.INSCRIPTION)
    if len(inscription_nodes) != 1:
        raise MetadataParseError("metadata enrichment requires exactly one inscription")
    inscription = inscription_nodes[0]
    inscription_key = inscription.key

    scalar = _scalar_metadata(root)
    inscription_features = dict(inscription.features)
    inscription_features.update(scalar)
    replacement = replace(
        inscription,
        features=tuple(sorted(inscription_features.items())),
    )

    nodes = [replacement if node.key == inscription.key else node for node in ir.nodes]
    edges = list(ir.edges)
    existing_keys = {node.key for node in nodes}

    def key_for(element: ET.Element) -> str:
        key = _source_key(
            element,
            inscription_id=ir.identity.inscription_id,
            paths=paths,
        )
        if key in existing_keys:
            raise MetadataParseError(f"duplicate IR source key {key!r}")
        existing_keys.add(key)
        return key

    # Physical support children in source order.
    for support in root.findall(
        ".//tei:objectDesc/tei:supportDesc/tei:support", _NS
    ):
        for element in list(support):
            name = _local(element.tag)
            if name == "p":
                note = _metadata_text(
                    element,
                    allowed_children={"foreign"},
                )
                if note is None:
                    continue
                key = key_for(element)
                node = _make_node(
                    key=key,
                    node_type=NodeType.SUPPORT_NOTE,
                    anchor=anchor,
                    features={"source_key": key, "note": note},
                )
                _add_owned(
                    nodes=nodes,
                    edges=edges,
                    node=node,
                    inscription_key=inscription_key,
                )
            elif name == "dimensions":
                key = key_for(element)
                node = _make_node(
                    key=key,
                    node_type=NodeType.DIMENSION,
                    anchor=anchor,
                    features=_dimension_features(
                        element,
                        source_key=key,
                    ),
                )
                _add_owned(
                    nodes=nodes,
                    edges=edges,
                    node=node,
                    inscription_key=inscription_key,
                )

    # Hand records and their dimensions.
    for hand_desc in root.findall(".//tei:physDesc/tei:handDesc", _NS):
        _validate_attrs(hand_desc)
        _validate_children(hand_desc, {"handNote"})
    for hand_note in root.findall(".//tei:physDesc/tei:handDesc/tei:handNote", _NS):
        _validate_attrs(hand_note)
        _validate_children(hand_note, {"p", "dimensions"})
        hand_key = key_for(hand_note)
        hand_features: dict[str, str | int] = {"source_key": hand_key}
        _append_feature(hand_features, "source_id", hand_note.attrib.get(XML_ID))
        _append_feature(hand_features, "technique", hand_note.attrib.get("ana"))
        hand_paragraphs = [
            child
            for child in list(hand_note)
            if _local(child.tag) == "p"
        ]
        _append_feature(
            hand_features,
            "note",
            _scalar(
                "hand note",
                [
                    value
                    for element in hand_paragraphs
                    if (value := _metadata_text(element))
                ],
            ),
        )
        hand_node = _make_node(
            key=hand_key,
            node_type=NodeType.HAND,
            anchor=anchor,
            features=hand_features,
        )
        _add_owned(
            nodes=nodes,
            edges=edges,
            node=hand_node,
            inscription_key=inscription_key,
        )

        for dimension in [
            child
            for child in list(hand_note)
            if _local(child.tag) == "dimensions"
        ]:
            dim_key = key_for(dimension)
            dim_node = _make_node(
                key=dim_key,
                node_type=NodeType.DIMENSION,
                anchor=anchor,
                features=_dimension_features(
                    dimension,
                    source_key=dim_key,
                ),
            )
            _add_owned(
                nodes=nodes,
                edges=edges,
                node=dim_node,
                inscription_key=inscription_key,
                parent=hand_key,
            )

    # Bibliography and nested scopes.
    bibl_by_id: dict[str, str] = {}
    bibliography_divs = root.findall(".//tei:div[@type='bibliography']", _NS)
    for element in bibliography_divs:
        _validate_attrs(element)
        _validate_children(element, {"listBibl"})
    for list_bibl in root.findall(
        ".//tei:div[@type='bibliography']/tei:listBibl", _NS
    ):
        _validate_attrs(list_bibl)
        _validate_children(list_bibl, {"bibl"})
    bibls = root.findall(
        ".//tei:div[@type='bibliography']/tei:listBibl/tei:bibl", _NS
    )
    for bibl in bibls:
        _validate_attrs(bibl)
        allowed_children = {"ptr", "biblScope"}
        unknown = [
            _local(child.tag)
            for child in list(bibl)
            if _local(child.tag) not in allowed_children
        ]
        if unknown:
            raise MetadataParseError(
                f"bibl: unsupported children {unknown!r}"
            )
        ptrs = [child for child in list(bibl) if _local(child.tag) == "ptr"]
        if len(ptrs) > 1:
            raise MetadataParseError("bibl: multiple ptr children")
        bibl_key = key_for(bibl)
        bibl_features: dict[str, str | int] = {"source_key": bibl_key}
        source_id = bibl.attrib.get(XML_ID)
        _append_feature(bibl_features, "source_id", source_id)
        if ptrs:
            ptr = ptrs[0]
            _validate_attrs(ptr)
            _append_feature(bibl_features, "target", ptr.attrib.get("target"))
            _append_feature(bibl_features, "ptr_type", ptr.attrib.get("type"))
        node = _make_node(
            key=bibl_key,
            node_type=NodeType.BIBL,
            anchor=anchor,
            features=bibl_features,
        )
        _add_owned(
            nodes=nodes,
            edges=edges,
            node=node,
            inscription_key=inscription_key,
        )
        if source_id:
            if source_id in bibl_by_id:
                raise MetadataParseError(
                    f"duplicate bibliography xml:id {source_id!r}"
                )
            bibl_by_id[source_id] = bibl_key

        for scope in [
            child for child in list(bibl) if _local(child.tag) == "biblScope"
        ]:
            _validate_attrs(scope)
            scope_key = key_for(scope)
            scope_features: dict[str, str | int] = {"source_key": scope_key}
            _append_feature(scope_features, "source_id", scope.attrib.get(XML_ID))
            _append_feature(scope_features, "scope", _metadata_text(scope))
            _append_feature(scope_features, "scope_unit", scope.attrib.get("unit"))
            _append_feature(scope_features, "scope_n", scope.attrib.get("n"))
            scope_node = _make_node(
                key=scope_key,
                node_type=NodeType.BIBL_SCOPE,
                anchor=anchor,
                features=scope_features,
            )
            _add_owned(
                nodes=nodes,
                edges=edges,
                node=scope_node,
                inscription_key=inscription_key,
                parent=bibl_key,
            )

    # Decorations.
    for deco_desc in root.findall(".//tei:physDesc/tei:decoDesc", _NS):
        _validate_attrs(deco_desc)
        _validate_children(deco_desc, {"decoNote"})
    for deco in root.findall(".//tei:physDesc/tei:decoDesc/tei:decoNote", _NS):
        _validate_attrs(deco)
        allowed = {"ab", "locus"}
        unknown = [
            _local(child.tag)
            for child in list(deco)
            if _local(child.tag) not in allowed
        ]
        if unknown:
            raise MetadataParseError(
                f"decoNote: unsupported children {unknown!r}"
            )
        key = key_for(deco)
        features: dict[str, str | int] = {"source_key": key}
        _append_feature(features, "source_id", deco.attrib.get(XML_ID))
        _append_feature(features, "type", deco.attrib.get("ana"))
        descriptions = [
            value
            for child in list(deco)
            if _local(child.tag) == "ab"
            and (value := _metadata_text(child))
        ]
        loci = [
            value
            for child in list(deco)
            if _local(child.tag) == "locus"
            and (value := _metadata_text(child))
        ]
        _append_feature(
            features,
            "description",
            _scalar("decoration description", descriptions),
        )
        _append_feature(
            features,
            "decoration_locus",
            _scalar("decoration locus", loci),
        )
        node = _make_node(
            key=key,
            node_type=NodeType.DECORATION,
            anchor=anchor,
            features=features,
        )
        _add_owned(
            nodes=nodes,
            edges=edges,
            node=node,
            inscription_key=inscription_key,
        )

    # Facsimile surfaces, direct images, and explicit credits.
    def add_image(
        graphic: ET.Element,
        *,
        parent_key: str,
        description: str | None = None,
        note: str | None = None,
        credit: str | None = None,
        credit_role: str | None = None,
    ) -> None:
        _validate_attrs(graphic)
        image_key = key_for(graphic)
        image_features: dict[str, str | int] = {"source_key": image_key}
        _append_feature(image_features, "source_id", graphic.attrib.get(XML_ID))
        _append_feature(image_features, "url", graphic.attrib.get("url"))
        _append_feature(image_features, "description", description)
        _append_feature(image_features, "note", note)
        _append_feature(image_features, "credit", credit)
        _append_feature(image_features, "credit_role", credit_role)
        image_node = _make_node(
            key=image_key,
            node_type=NodeType.IMAGE,
            anchor=anchor,
            features=image_features,
        )
        _add_owned(
            nodes=nodes,
            edges=edges,
            node=image_node,
            inscription_key=inscription_key,
            parent=parent_key,
        )

    def add_surface(
        surface: ET.Element,
        *,
        parent_key: str,
        depth: int,
    ) -> None:
        if depth > 2:
            raise MetadataParseError(
                f"surface depth {depth} exceeds frozen schema maximum 2"
            )
        _validate_attrs(surface)
        allowed_surface = {"desc", "graphic", "note", "surface"}
        unknown = [
            _local(item.tag)
            for item in list(surface)
            if _local(item.tag) not in allowed_surface
        ]
        if unknown:
            raise MetadataParseError(
                f"surface: unsupported children {unknown!r}"
            )
        surface_key = key_for(surface)
        descriptions = [
            item for item in list(surface) if _local(item.tag) == "desc"
        ]
        notes = [
            item for item in list(surface) if _local(item.tag) == "note"
        ]
        for item in [*descriptions, *notes]:
            _validate_attrs(item)
        description = _scalar(
            "facsimile surface description",
            [
                value
                for item in descriptions
                if (
                    value := _metadata_text(
                        item,
                        allowed_children={"persName"},
                    )
                )
            ],
        )
        note = _scalar(
            "facsimile surface note",
            [
                value
                for item in notes
                if (value := _metadata_text(item))
            ],
        )
        surface_features: dict[str, str | int] = {"source_key": surface_key}
        _append_feature(surface_features, "source_id", surface.attrib.get(XML_ID))
        _append_feature(surface_features, "description", description)
        _append_feature(surface_features, "note", note)
        surface_node = _make_node(
            key=surface_key,
            node_type=NodeType.FACSIMILE_SURFACE,
            anchor=anchor,
            features=surface_features,
        )
        _add_owned(
            nodes=nodes,
            edges=edges,
            node=surface_node,
            inscription_key=inscription_key,
            parent=parent_key,
        )

        credit_elements: list[ET.Element] = []
        for desc in descriptions:
            for descendant in desc.iter():
                if _local(descendant.tag) == "persName":
                    _validate_attrs(descendant)
                    if descendant.attrib.get("role"):
                        credit_elements.append(descendant)
        credit = _scalar(
            "image credit",
            [
                value
                for item in credit_elements
                if (value := _metadata_text(item))
            ],
        )
        credit_role = _scalar(
            "image credit role",
            _values(credit_elements, "role"),
        )

        for item in list(surface):
            name = _local(item.tag)
            if name == "graphic":
                add_image(
                    item,
                    parent_key=surface_key,
                    description=description,
                    note=note,
                    credit=credit,
                    credit_role=credit_role,
                )
            elif name == "surface":
                add_surface(item, parent_key=surface_key, depth=depth + 1)

    for facsimile in root.findall(".//tei:facsimile", _NS):
        _validate_attrs(facsimile)
        for child in list(facsimile):
            name = _local(child.tag)
            if name == "graphic":
                add_image(child, parent_key=inscription_key)
            elif name == "surface":
                add_surface(child, parent_key=inscription_key, depth=1)
            else:
                raise MetadataParseError(
                    f"facsimile: unsupported child {name!r}"
                )

    # Revision history.
    for revision_desc in root.findall(".//tei:teiHeader/tei:revisionDesc", _NS):
        _validate_attrs(revision_desc)
        for change in list(revision_desc):
            if _local(change.tag) != "change":
                raise MetadataParseError(
                    f"revisionDesc: unsupported child {_local(change.tag)!r}"
                )
            _validate_attrs(change)
            key = key_for(change)
            revision_features: dict[str, str | int] = {"source_key": key}
            _append_feature(
                revision_features, "source_id", change.attrib.get(XML_ID)
            )
            _append_feature(revision_features, "when", change.attrib.get("when"))
            _append_feature(
                revision_features, "when_custom", change.attrib.get("when-custom")
            )
            _append_feature(revision_features, "who", change.attrib.get("who"))
            _append_feature(
                revision_features,
                "description",
                _metadata_text(change),
            )
            node = _make_node(
                key=key,
                node_type=NodeType.REVISION,
                anchor=anchor,
                features=revision_features,
            )
            _add_owned(
                nodes=nodes,
                edges=edges,
                node=node,
                inscription_key=inscription_key,
            )

    # Resolve raw textual ana/entity ana only when the target is a local bibl id.
    existing_edge_keys = {
        (edge.edge_type, edge.source, edge.target) for edge in edges
    }
    for node in nodes:
        raw = node.feature("source_ana")
        if raw is None:
            raw = node.feature("ana")
        if not isinstance(raw, str):
            continue
        for token in raw.split():
            target_id = token[1:] if token.startswith("#") else token
            target = bibl_by_id.get(target_id)
            if target is None:
                continue
            edge_key = (EdgeType.CITES, node.key, target)
            if edge_key not in existing_edge_keys:
                edges.append(IREdge(*edge_key))
                existing_edge_keys.add(edge_key)

    return InscriptionIR(
        identity=ir.identity,
        provenance=ir.provenance,
        signs=ir.signs,
        nodes=tuple(nodes),
        edges=tuple(edges),
        diagnostics=ir.diagnostics,
    )
