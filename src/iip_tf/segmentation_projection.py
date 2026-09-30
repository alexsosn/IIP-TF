"""Project selected IIP segmented tokens onto existing primary-text signs."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from typing import Final, TypeAlias

from iip_tf.ir import EdgeType, InscriptionIR, IREdge, IRNode, NodeType
from iip_tf.segmentation import SegmentationResolution, resolve_segmented_root

TEI_NS: Final = "http://www.tei-c.org/ns/1.0"
XML_NS: Final = "http://www.w3.org/XML/1998/namespace"
XML_ID: Final = f"{{{XML_NS}}}id"
XML_LANG: Final = f"{{{XML_NS}}}lang"

Atom: TypeAlias = tuple[str, str, str]

_TOKEN_TAGS: Final = {"w", "num", "orig"}
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
_EVENT_KIND: Final = {
    "cb": "column_break",
    "figure": "figure",
    "gap": "gap",
    "handShift": "hand_shift",
    "milestone": "milestone",
    "space": "space",
}
_SEGMENTED_ATTRS: Final[dict[str, frozenset[str]]] = {
    "w": frozenset({"xml:id", "xml:lang"}),
    "num": frozenset({"value", "xml:id", "xml:lang"}),
    "orig": frozenset({"xml:id", "xml:lang"}),
    "abbr": frozenset(),
    "add": frozenset({"place"}),
    "am": frozenset(),
    "app": frozenset({"type"}),
    "cb": frozenset(),
    "choice": frozenset(),
    "corr": frozenset(),
    "del": frozenset({"extent", "rend"}),
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
    "hi": frozenset({"rend"}),
    "lem": frozenset(),
    "milestone": frozenset({"n", "unit"}),
    "rdg": frozenset(),
    "reg": frozenset(),
    "sic": frozenset(),
    "space": frozenset({"dim", "extent", "quantity", "unit"}),
    "subst": frozenset(),
    "supplied": frozenset({"cert", "evidence", "extent", "reason", "unit"}),
    "surplus": frozenset({"cert"}),
    "unclear": frozenset({"cert", "reason"}),
}
_ATTR_FEATURE: Final = {
    "atLeast": "at_least",
    "atMost": "at_most",
    "break": "break",
    "cert": "cert",
    "dim": "dim",
    "evidence": "evidence",
    "extent": "extent",
    "n": "source_n",
    "new": "new_hand",
    "place": "place",
    "precision": "precision",
    "quantity": "quantity",
    "reason": "reason",
    "ref": "ref",
    "rend": "rend",
    "type": "type",
    "unit": "unit",
    "value": "value",
}


class SegmentationProjectionError(ValueError):
    """Raised when selected segmentation cannot be projected without guessing."""


@dataclass(frozen=True)
class _PrimaryAtom:
    signature: Atom
    sign_index: int


@dataclass(frozen=True)
class _AnnotationSpec:
    key: str
    start: int
    end: int
    features: tuple[tuple[str, str | int], ...]
    parent_key: str | None


@dataclass(frozen=True)
class _TokenSpec:
    element: ET.Element
    atoms: tuple[Atom, ...]
    annotations: tuple[_AnnotationSpec, ...]


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


def _validate_attrs(element: ET.Element) -> None:
    name = _local(element.tag)
    allowed = _SEGMENTED_ATTRS.get(name)
    if allowed is None:
        raise SegmentationProjectionError(
            f"unsupported segmented element {name!r}"
        )
    for raw_name in element.attrib:
        attr = _attr_name(raw_name)
        if attr not in allowed:
            raise SegmentationProjectionError(
                f"unsupported segmented attribute {name}@{attr}"
            )


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


def _segmented_divs(root: ET.Element) -> tuple[ET.Element, ...]:
    return tuple(
        element
        for element in root.iter(f"{{{TEI_NS}}}div")
        if element.attrib.get("type") == "edition"
        and element.attrib.get("subtype") == "transcription_segmented"
    )


def _tokens(div: ET.Element) -> tuple[ET.Element, ...]:
    result: list[ET.Element] = []
    for paragraph in div.iter(f"{{{TEI_NS}}}p"):
        for child in list(paragraph):
            if _local(child.tag) in _TOKEN_TAGS:
                result.append(child)
    return tuple(result)


def _append_text(atoms: list[Atom], text: str | None, *, role: str) -> None:
    if not text:
        return
    for char in text:
        if not char.isspace():
            atoms.append(("char", char, role))


def _annotation_features(
    element: ET.Element,
    *,
    source_key: str,
    layer: str,
) -> dict[str, str | int]:
    name = _local(element.tag)
    features: dict[str, str | int] = {
        "source_key": source_key,
        "kind": _MARKUP_KIND[name],
        "layer": layer,
        "annotation_source": "transcription_segmented",
    }
    source_id = element.attrib.get(XML_ID)
    if source_id:
        features["source_id"] = source_id
    for raw_name, raw_value in element.attrib.items():
        attr = _attr_name(raw_name)
        if attr == "xml:id":
            continue
        if attr == "xml:lang":
            features["lang"] = raw_value.strip()
            features["lang_source"] = "transcription_segmented"
            continue
        mapped = _ATTR_FEATURE.get(attr)
        if mapped:
            features[mapped] = raw_value
    if name == "figure":
        descriptions = [
            " ".join("".join(child.itertext()).split())
            for child in list(element)
            if _local(child.tag) == "figDesc"
        ]
        description = " ".join(value for value in descriptions if value)
        if description:
            features["description"] = description
    return features


def _token_spec(
    token: ET.Element,
    *,
    record_id: str,
    candidate_index: int,
    paths: dict[int, str],
    layer: str,
) -> _TokenSpec:
    root_name = _local(token.tag)
    if root_name not in _TOKEN_TAGS:
        raise SegmentationProjectionError(
            f"{record_id}: non-token child {root_name!r} in selected segmentation"
        )
    _validate_attrs(token)
    atoms: list[Atom] = []
    annotations: list[_AnnotationSpec] = []

    def visit(
        element: ET.Element,
        *,
        role: str,
        parent_key: str | None,
        token_root: bool = False,
    ) -> None:
        name = _local(element.tag)
        if name == "figDesc":
            _validate_attrs(element)
            return
        _validate_attrs(element)

        semantic = not (token_root and name == "w")
        if name not in _MARKUP_KIND and not (token_root and name == "w"):
            raise SegmentationProjectionError(
                f"{record_id}: unsupported segmented inline element {name!r}"
            )

        local_role = _ROLE.get(name, "both")
        current_role = _combine_role(role, local_role)
        key: str | None = None
        if semantic:
            key = (
                f"{record_id}#segann:{candidate_index}:"
                f"{paths[id(element)]}"
            )
        start = len(atoms)

        if name == "figure":
            atoms.append(("event", "figure", current_role))
        elif name in _EVENT_KIND:
            atoms.append(("event", _EVENT_KIND[name], current_role))
        elif name == "g" and not (
            (element.text and element.text.strip()) or list(element)
        ):
            atoms.append(("event", "glyph_ref", current_role))
        else:
            _append_text(atoms, element.text, role=current_role)
            for child in list(element):
                visit(
                    child,
                    role=current_role,
                    parent_key=key if key is not None else parent_key,
                )
                _append_text(atoms, child.tail, role=current_role)

        end = len(atoms)
        if semantic:
            assert key is not None
            if end <= start:
                raise SegmentationProjectionError(
                    f"{record_id}: segmented markup {name!r} has no projection atoms"
                )
            features = _annotation_features(
                element,
                source_key=(
                    f"{record_id}#path:{paths[id(element)]}"
                ),
                layer=layer,
            )
            annotations.append(
                _AnnotationSpec(
                    key=key,
                    start=start,
                    end=end,
                    features=tuple(sorted(features.items())),
                    parent_key=parent_key,
                )
            )

    root_role = "source" if root_name == "orig" else "both"
    visit(token, role=root_role, parent_key=None, token_root=True)
    if not atoms:
        token_id = token.attrib.get(XML_ID, "<missing>")
        raise SegmentationProjectionError(
            f"{record_id}: selected token {token_id!r} has no projection atoms"
        )
    return _TokenSpec(
        element=token,
        atoms=tuple(atoms),
        annotations=tuple(annotations),
    )


def _primary_atoms(ir: InscriptionIR, *, primary_layer: str) -> tuple[_PrimaryAtom, ...]:
    atoms: list[_PrimaryAtom] = []
    for index, sign in enumerate(ir.signs):
        if sign.layer.value != primary_layer:
            continue
        if sign.synthetic_kind == "line_break":
            continue
        if sign.synthetic_kind is not None:
            signature: Atom = (
                "event",
                sign.synthetic_kind,
                sign.reading_role,
            )
        else:
            signature = ("char", sign.glyph, sign.reading_role)
        atoms.append(_PrimaryAtom(signature=signature, sign_index=index))
    return tuple(atoms)


def _matches(
    primary: tuple[_PrimaryAtom, ...],
    signature: tuple[Atom, ...],
) -> tuple[tuple[int, int], ...]:
    width = len(signature)
    if width == 0:
        return ()
    return tuple(
        (start, start + width)
        for start in range(0, len(primary) - width + 1)
        if tuple(atom.signature for atom in primary[start : start + width])
        == signature
    )


def _unique_embedding(
    primary: tuple[_PrimaryAtom, ...],
    tokens: tuple[_TokenSpec, ...],
    *,
    record_id: str,
) -> tuple[tuple[int, int], ...]:
    if not tokens:
        return ()
    choices = tuple(_matches(primary, token.atoms) for token in tokens)
    if any(not matches for matches in choices):
        missing = next(index for index, matches in enumerate(choices) if not matches)
        token_id = tokens[missing].element.attrib.get(XML_ID, "<missing>")
        raise SegmentationProjectionError(
            f"{record_id}: no projection for token {token_id!r}"
        )

    suffix_counts: list[list[int]] = [
        [0 for _ in matches] for matches in choices
    ]
    suffix_counts[-1] = [1 for _ in choices[-1]]
    for token_index in range(len(tokens) - 2, -1, -1):
        next_matches = choices[token_index + 1]
        next_counts = suffix_counts[token_index + 1]
        for match_index, (_, end) in enumerate(choices[token_index]):
            count = 0
            for next_index, (next_start, _) in enumerate(next_matches):
                if next_start < end:
                    continue
                count += next_counts[next_index]
                if count >= 2:
                    count = 2
                    break
            suffix_counts[token_index][match_index] = count

    total = min(2, sum(suffix_counts[0]))
    if total == 0:
        raise SegmentationProjectionError(
            f"{record_id}: no complete monotonic token projection"
        )
    if total > 1:
        raise SegmentationProjectionError(
            f"{record_id}: ambiguous complete monotonic token projection"
        )

    result: list[tuple[int, int]] = []
    minimum_start = 0
    for token_index, token_matches in enumerate(choices):
        viable = [
            match
            for match_index, match in enumerate(token_matches)
            if match[0] >= minimum_start
            and suffix_counts[token_index][match_index] > 0
        ]
        if len(viable) != 1:
            raise SegmentationProjectionError(
                f"{record_id}: ambiguous projection while reconstructing token sequence"
            )
        selected = viable[0]
        result.append(selected)
        minimum_start = selected[1]
    return tuple(result)


def _word_text(token: ET.Element) -> str:
    def collect(
        element: ET.Element,
        *,
        in_choice: bool = False,
        in_expan: bool = False,
    ) -> str:
        name = _local(element.tag)
        if (in_choice and name in {"sic", "orig"}) or (
            in_expan and name == "am"
        ):
            return ""
        if name in {"surplus", "g"}:
            return ""
        parts: list[str] = [element.text or ""]
        next_choice = in_choice or name == "choice"
        next_expan = in_expan or name == "expan"
        for child in list(element):
            parts.append(
                collect(
                    child,
                    in_choice=next_choice,
                    in_expan=next_expan,
                )
            )
            parts.append(child.tail or "")
        return "".join(parts)

    return " ".join(collect(token).split())


def _candidate_languages(candidate: ET.Element) -> str | None:
    langs = sorted(
        {
            value.strip()
            for token in _tokens(candidate)
            if (value := token.attrib.get(XML_LANG))
            and value.strip()
        }
    )
    return " ".join(langs) if langs else None


def _target_edition(ir: InscriptionIR, *, primary_layer: str) -> IRNode | None:
    editions = ir.nodes_of_type(NodeType.EDITION)
    preferred = [
        node
        for node in editions
        if node.feature("edition_kind") == primary_layer
    ]
    if primary_layer != "empty":
        if len(preferred) != 1:
            raise SegmentationProjectionError(
                f"{ir.identity.inscription_id}: expected one primary {primary_layer} edition"
            )
        return preferred[0]

    transcription = [
        node
        for node in editions
        if node.feature("edition_kind") == "transcription"
    ]
    if len(transcription) > 1:
        raise SegmentationProjectionError(
            f"{ir.identity.inscription_id}: multiple transcription editions"
        )
    if transcription:
        return transcription[0]
    diplomatic = [
        node
        for node in editions
        if node.feature("edition_kind") == "diplomatic"
    ]
    return diplomatic[0] if len(diplomatic) == 1 else None


def _technical_anchor(ir: InscriptionIR, *, primary_layer: str) -> str:
    if primary_layer != "empty":
        for sign in ir.signs:
            if sign.layer.value == primary_layer:
                return sign.key
    for sign in ir.signs:
        if sign.synthetic_kind == "anchor":
            return sign.key
    if ir.signs:
        return ir.signs[0].key
    raise SegmentationProjectionError(
        f"{ir.identity.inscription_id}: no sign available for segmentation provenance"
    )


def enrich_segmentation(
    ir: InscriptionIR,
    root: ET.Element,
    *,
    source_revision: str,
) -> InscriptionIR:
    """Add candidate provenance, projected words, and segmented markup annotations."""

    record_id = ir.identity.inscription_id
    candidates = _segmented_divs(root)
    if not candidates:
        return ir

    resolution: SegmentationResolution = resolve_segmented_root(
        root,
        source_revision=source_revision,
        record_id=record_id,
    )
    inscription_nodes = ir.nodes_of_type(NodeType.INSCRIPTION)
    if len(inscription_nodes) != 1:
        raise SegmentationProjectionError(
            f"{record_id}: segmentation requires one inscription node"
        )
    inscription = inscription_nodes[0]
    primary_raw = inscription.feature("primary_layer")
    if not isinstance(primary_raw, str):
        raise SegmentationProjectionError(
            f"{record_id}: inscription has no primary_layer"
        )
    primary_layer = primary_raw
    target = _target_edition(ir, primary_layer=primary_layer)
    anchor = _technical_anchor(ir, primary_layer=primary_layer)
    paths = _paths(root)

    nodes = list(ir.nodes)
    edges = list(ir.edges)
    existing_keys = {node.key for node in nodes}
    candidate_keys: list[str] = []

    for index, candidate in enumerate(candidates):
        key = f"{record_id}#segmentation:{index}"
        if key in existing_keys:
            raise SegmentationProjectionError(
                f"{record_id}: duplicate segmentation key {key!r}"
            )
        existing_keys.add(key)
        candidate_keys.append(key)
        features: dict[str, str | int] = {
            "source_key": f"{record_id}#path:{paths[id(candidate)]}",
            "candidate_index": index,
            "selected": int(index == resolution.selected_index),
            "resolution_status": resolution.status,
            "token_count": len(_tokens(candidate)),
        }
        change = candidate.attrib.get("change")
        if change:
            features["source_change"] = change
        languages = _candidate_languages(candidate)
        if languages:
            features["candidate_langs"] = languages
        if resolution.conflict_fields:
            features["conflict_fields"] = " ".join(resolution.conflict_fields)
        nodes.append(
            IRNode(
                key=key,
                node_type=NodeType.SEGMENTATION,
                sign_keys=(anchor,),
                features=tuple(sorted(features.items())),
            )
        )
        edges.append(
            IREdge(EdgeType.IN_INSCRIPTION, key, inscription.key)
        )
        if target is not None:
            edges.append(
                IREdge(EdgeType.SEGMENTATION_OF, key, target.key)
            )

    if resolution.selected_index is None:
        return InscriptionIR(
            identity=ir.identity,
            provenance=ir.provenance,
            signs=ir.signs,
            nodes=tuple(nodes),
            edges=tuple(edges),
            diagnostics=ir.diagnostics,
        )

    selected = candidates[resolution.selected_index]
    token_elements = _tokens(selected)
    if not token_elements:
        return InscriptionIR(
            identity=ir.identity,
            provenance=ir.provenance,
            signs=ir.signs,
            nodes=tuple(nodes),
            edges=tuple(edges),
            diagnostics=ir.diagnostics,
        )
    if primary_layer == "empty":
        raise SegmentationProjectionError(
            f"{record_id}: non-empty selected segmentation has no primary source text"
        )

    token_ids = [token.attrib.get(XML_ID) for token in token_elements]
    if any(not token_id for token_id in token_ids):
        raise SegmentationProjectionError(
            f"{record_id}: selected segmentation token lacks xml:id"
        )
    if len(set(token_ids)) != len(token_ids):
        raise SegmentationProjectionError(
            f"{record_id}: duplicate token ids in selected segmentation"
        )

    specs = tuple(
        _token_spec(
            token,
            record_id=record_id,
            candidate_index=resolution.selected_index,
            paths=paths,
            layer=primary_layer,
        )
        for token in token_elements
    )
    primary = _primary_atoms(ir, primary_layer=primary_layer)
    embedding = _unique_embedding(primary, specs, record_id=record_id)
    selected_candidate_key = candidate_keys[resolution.selected_index]

    for spec, (start, end) in zip(specs, embedding, strict=True):
        first_sign = primary[start].sign_index
        last_sign = primary[end - 1].sign_index
        sign_keys = tuple(
            sign.key
            for sign in ir.signs[first_sign : last_sign + 1]
            if sign.layer.value == primary_layer
        )
        token = spec.element
        token_id = token.attrib[XML_ID]
        word_key = f"{record_id}#word:{token_id}"
        if word_key in existing_keys:
            raise SegmentationProjectionError(
                f"{record_id}: duplicate word key {word_key!r}"
            )
        existing_keys.add(word_key)
        word_features: dict[str, str | int] = {
            "source_id": token_id,
            "source_key": f"{record_id}#path:{paths[id(token)]}",
            "token_kind": _local(token.tag),
            "token_id": token_id,
            "word_text": _word_text(token),
            "segmentation_status": "projected",
            "candidate_index": resolution.selected_index,
        }
        lang = token.attrib.get(XML_LANG)
        if lang:
            word_features["lang"] = lang.strip()
            word_features["lang_source"] = "transcription_segmented"
        if "value" in token.attrib:
            word_features["value"] = token.attrib["value"]
        nodes.append(
            IRNode(
                key=word_key,
                node_type=NodeType.WORD,
                sign_keys=sign_keys,
                features=tuple(sorted(word_features.items())),
            )
        )
        edges.append(
            IREdge(EdgeType.TOKEN_FROM, word_key, selected_candidate_key)
        )

        primary_slice = primary[start:end]
        for annotation in spec.annotations:
            ann_first = primary_slice[annotation.start].sign_index
            ann_last = primary_slice[annotation.end - 1].sign_index
            ann_sign_keys = tuple(
                sign.key
                for sign in ir.signs[ann_first : ann_last + 1]
                if sign.layer.value == primary_layer
            )
            if annotation.key in existing_keys:
                raise SegmentationProjectionError(
                    f"{record_id}: duplicate projected annotation key "
                    f"{annotation.key!r}"
                )
            existing_keys.add(annotation.key)
            nodes.append(
                IRNode(
                    key=annotation.key,
                    node_type=NodeType.MARKUP,
                    sign_keys=ann_sign_keys,
                    features=annotation.features,
                )
            )
            if annotation.parent_key is not None:
                edges.append(
                    IREdge(
                        EdgeType.PARENT,
                        annotation.key,
                        annotation.parent_key,
                    )
                )

    return InscriptionIR(
        identity=ir.identity,
        provenance=ir.provenance,
        signs=ir.signs,
        nodes=tuple(nodes),
        edges=tuple(dict.fromkeys(edges)),
        diagnostics=ir.diagnostics,
    )
