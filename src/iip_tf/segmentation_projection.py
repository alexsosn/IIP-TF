"""Project selected IIP segmented tokens onto existing primary-text signs."""

from __future__ import annotations

import unicodedata
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

Atom: TypeAlias = tuple[str, str, str, str | None]

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
    sign_start: int
    sign_end: int


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


@dataclass(frozen=True)
class _TokenMatch:
    start: int
    end: int
    cost: int
    drift_edits: int
    positions: tuple[int | None, ...]


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
            atoms.append(("char", char, role, None))


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
            atoms.append(("event", "figure", current_role, None))
        elif name in _EVENT_KIND:
            atoms.append(("event", _EVENT_KIND[name], current_role, None))
        elif name == "g":
            display = "".join(element.itertext()).strip()
            atoms.append(
                ("glyph", display, current_role, element.attrib.get("ref"))
            )
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
        top_level = [
            (index, annotation)
            for index, annotation in enumerate(annotations)
            if annotation.parent_key is None
        ]
        if len(annotations) != 1 or len(top_level) != 1:
            raise SegmentationProjectionError(
                f"{record_id}: zero-atom token {token_id!r} has no unique annotation target"
            )
        index, annotation = top_level[0]
        features = dict(annotation.features)
        features["token_id"] = token_id
        features["token_kind"] = root_name
        features["candidate_index"] = candidate_index
        lang = token.attrib.get(XML_LANG)
        if lang:
            features["lang"] = lang.strip()
            features["lang_source"] = "transcription_segmented"
        if "value" in token.attrib:
            features["value"] = token.attrib["value"]
        annotations[index] = _AnnotationSpec(
            key=annotation.key,
            start=annotation.start,
            end=annotation.end,
            features=tuple(sorted(features.items())),
            parent_key=annotation.parent_key,
        )
    return _TokenSpec(
        element=token,
        atoms=tuple(atoms),
        annotations=tuple(annotations),
    )


def _first_primary_paragraph(
    ir: InscriptionIR,
    *,
    target: IRNode,
    primary_layer: str,
) -> IRNode:
    parent_of = {
        edge.source: edge.target
        for edge in ir.edges
        if edge.edge_type == EdgeType.PARENT
    }

    def belongs_to_target(node: IRNode) -> bool:
        current = node.key
        seen: set[str] = set()
        while current in parent_of:
            if current in seen:
                raise SegmentationProjectionError(
                    f"{ir.identity.inscription_id}: parent cycle in textual IR"
                )
            seen.add(current)
            current = parent_of[current]
            if current == target.key:
                return True
        return False

    paragraphs = [
        node
        for node in ir.nodes
        if node.node_type == NodeType.PARAGRAPH
        and node.feature("layer") == primary_layer
        and node.feature("kind") == "p"
        and belongs_to_target(node)
    ]
    if not paragraphs:
        raise SegmentationProjectionError(
            f"{ir.identity.inscription_id}: selected segmentation has no source paragraph"
        )
    return paragraphs[0]


def _primary_atoms(
    ir: InscriptionIR,
    *,
    primary_layer: str,
    target: IRNode,
) -> tuple[_PrimaryAtom, ...]:
    paragraph = _first_primary_paragraph(
        ir,
        target=target,
        primary_layer=primary_layer,
    )
    scope = set(paragraph.sign_keys)
    index_by_key = {sign.key: index for index, sign in enumerate(ir.signs)}

    glyph_ranges: dict[int, tuple[int, str]] = {}
    for node in ir.nodes:
        if (
            node.node_type != NodeType.MARKUP
            or node.feature("kind") != "glyph"
            or not node.sign_keys
        ):
            continue
        if not set(node.sign_keys) <= scope:
            continue
        indices = sorted(index_by_key[key] for key in node.sign_keys)
        if indices != list(range(indices[0], indices[-1] + 1)):
            raise SegmentationProjectionError(
                f"{ir.identity.inscription_id}: non-contiguous glyph source span"
            )
        if indices[0] in glyph_ranges:
            raise SegmentationProjectionError(
                f"{ir.identity.inscription_id}: overlapping glyph source spans"
            )
        ref = node.feature("ref")
        glyph_ranges[indices[0]] = (
            indices[-1],
            ref if isinstance(ref, str) else "",
        )

    atoms: list[_PrimaryAtom] = []
    skip_until = -1
    for index, sign in enumerate(ir.signs):
        if index <= skip_until:
            continue
        if sign.key not in scope:
            continue
        if sign.layer.value != primary_layer:
            raise SegmentationProjectionError(
                f"{ir.identity.inscription_id}: paragraph crosses primary text layers"
            )

        glyph_range = glyph_ranges.get(index)
        if glyph_range is not None:
            glyph_end, glyph_ref = glyph_range
            roles = {
                ir.signs[item].reading_role
                for item in range(index, glyph_end + 1)
            }
            if len(roles) != 1:
                raise SegmentationProjectionError(
                    f"{ir.identity.inscription_id}: glyph span crosses reading roles"
                )
            display = "".join(
                ir.signs[item].glyph
                for item in range(index, glyph_end + 1)
            )
            atoms.append(
                _PrimaryAtom(
                    signature=(
                        "glyph",
                        display,
                        sign.reading_role,
                        glyph_ref or None,
                    ),
                    sign_start=index,
                    sign_end=glyph_end,
                )
            )
            skip_until = glyph_end
            continue

        if sign.synthetic_kind == "line_break":
            continue
        if sign.synthetic_kind is not None:
            signature: Atom = (
                "event",
                sign.synthetic_kind,
                sign.reading_role,
                None,
            )
        else:
            signature = ("char", sign.glyph, sign.reading_role, None)
        atoms.append(
            _PrimaryAtom(
                signature=signature,
                sign_start=index,
                sign_end=index,
            )
        )
    return tuple(atoms)


_GENERIC_SUBSTITUTION_COST: Final = 12
_SOURCE_INSERT_DELETE_COST: Final = 18
_MAX_SOURCE_DRIFT_EDITS: Final = 2


def _role_match_cost(primary_role: str, segmented_role: str) -> int:
    if primary_role == segmented_role:
        return 0
    if primary_role == "both" or segmented_role == "both":
        return 1
    return 4


def _atom_match_cost(primary: Atom, segmented: Atom) -> int | None:
    role_cost = _role_match_cost(primary[2], segmented[2])

    primary_kind, primary_value, _, primary_ref = primary
    segmented_kind, segmented_value, _, segmented_ref = segmented

    if segmented_ref is not None:
        if primary_kind != "glyph" or primary_ref != segmented_ref:
            return None
        return role_cost

    if segmented_kind == "glyph":
        if primary_kind == "glyph":
            if segmented_value and primary_value != segmented_value:
                return None
            return role_cost + 1
        if (
            segmented_value
            and primary_kind == "char"
            and primary_value == segmented_value
        ):
            return role_cost + 2
        return None

    if primary_kind == "glyph" and segmented_kind == "char":
        if primary_value and primary_value == segmented_value:
            return role_cost + 2
        return None

    if primary_kind != segmented_kind or primary_value != segmented_value:
        return None
    return role_cost


def _char_drift_cost(primary_value: str, segmented_value: str) -> int:
    if primary_value.casefold() == segmented_value.casefold():
        return 4

    def base(value: str) -> str:
        decomposed = unicodedata.normalize("NFD", value.casefold())
        return "".join(
            char
            for char in decomposed
            if unicodedata.category(char) != "Mn"
        )

    if base(primary_value) == base(segmented_value):
        return 6
    return _GENERIC_SUBSTITUTION_COST


def _atom_alignment_cost(primary: Atom, segmented: Atom) -> tuple[int, int] | None:
    exact = _atom_match_cost(primary, segmented)
    if exact is not None:
        return exact, 0

    if primary[0] == "char" and segmented[0] == "char":
        return (
            _char_drift_cost(primary[1], segmented[1])
            + _role_match_cost(primary[2], segmented[2]),
            1,
        )
    return None


def _matches(
    primary: tuple[_PrimaryAtom, ...],
    signature: tuple[Atom, ...],
) -> tuple[_TokenMatch, ...]:
    if not signature:
        return ()

    matches: list[_TokenMatch] = []
    for start, primary_atom in enumerate(primary):
        first = _atom_alignment_cost(primary_atom.signature, signature[0])
        if first is None:
            continue
        first_cost, first_drift = first
        if first_drift > _MAX_SOURCE_DRIFT_EDITS:
            continue

        states: list[tuple[int, int, int, tuple[int | None, ...]]] = [
            (start, first_cost, first_drift, (start,))
        ]
        for segmented_atom in signature[1:]:
            next_states: list[
                tuple[int, int, int, tuple[int | None, ...]]
            ] = []
            for current, accumulated, drift_edits, positions in states:
                if (
                    segmented_atom[0] == "char"
                    and drift_edits < _MAX_SOURCE_DRIFT_EDITS
                ):
                    next_states.append(
                        (
                            current,
                            accumulated + _SOURCE_INSERT_DELETE_COST,
                            drift_edits + 1,
                            (*positions, None),
                        )
                    )

                candidate = current + 1
                skipped_cost = 0
                skipped_drift = 0
                while candidate < len(primary):
                    aligned = _atom_alignment_cost(
                        primary[candidate].signature,
                        segmented_atom,
                    )
                    if aligned is not None:
                        match_cost, match_drift = aligned
                        total_drift = drift_edits + skipped_drift + match_drift
                        if total_drift <= _MAX_SOURCE_DRIFT_EDITS:
                            next_states.append(
                                (
                                    candidate,
                                    accumulated
                                    + skipped_cost
                                    + match_cost,
                                    total_drift,
                                    (*positions, candidate),
                                )
                            )

                    candidate_kind = primary[candidate].signature[0]
                    if candidate_kind == "glyph":
                        skipped_cost += 3
                    elif (
                        candidate_kind == "char"
                        and drift_edits + skipped_drift
                        < _MAX_SOURCE_DRIFT_EDITS
                    ):
                        skipped_cost += _SOURCE_INSERT_DELETE_COST
                        skipped_drift += 1
                    else:
                        break
                    candidate += 1
            states = next_states
            if not states:
                break

        for end_position, cost, drift_edits, positions in states:
            matches.append(
                _TokenMatch(
                    start=start,
                    end=end_position + 1,
                    cost=cost,
                    drift_edits=drift_edits,
                    positions=positions,
                )
            )
    return tuple(matches)


def _unique_embedding(
    primary: tuple[_PrimaryAtom, ...],
    tokens: tuple[_TokenSpec, ...],
    *,
    record_id: str,
) -> tuple[_TokenMatch, ...]:
    if not tokens:
        return ()

    choices = tuple(_matches(primary, token.atoms) for token in tokens)
    if any(not matches for matches in choices):
        missing = next(index for index, matches in enumerate(choices) if not matches)
        token_id = tokens[missing].element.attrib.get(XML_ID, "<missing>")
        raise SegmentationProjectionError(
            f"{record_id}: no projection for token {token_id!r}"
        )

    best_cost: list[list[int | None]] = [
        [None for _ in matches] for matches in choices
    ]
    best_count: list[list[int]] = [
        [0 for _ in matches] for matches in choices
    ]
    best_next: list[list[int | None]] = [
        [None for _ in matches] for matches in choices
    ]

    for match_index, match in enumerate(choices[-1]):
        best_cost[-1][match_index] = match.cost
        best_count[-1][match_index] = 1

    for token_index in range(len(tokens) - 2, -1, -1):
        next_matches = choices[token_index + 1]
        for match_index, match in enumerate(choices[token_index]):
            minimum: int | None = None
            count = 0
            selected_next: int | None = None
            for next_index, next_match in enumerate(next_matches):
                if next_match.start < match.end:
                    continue
                suffix_cost = best_cost[token_index + 1][next_index]
                if suffix_cost is None:
                    continue
                candidate = match.cost + suffix_cost
                if minimum is None or candidate < minimum:
                    minimum = candidate
                    count = best_count[token_index + 1][next_index]
                    selected_next = next_index
                elif candidate == minimum:
                    count = min(
                        2,
                        count + best_count[token_index + 1][next_index],
                    )
                    selected_next = None
            best_cost[token_index][match_index] = minimum
            best_count[token_index][match_index] = min(2, count)
            if count == 1:
                best_next[token_index][match_index] = selected_next

    complete = [
        (index, cost)
        for index, cost in enumerate(best_cost[0])
        if cost is not None and best_count[0][index] > 0
    ]
    if not complete:
        raise SegmentationProjectionError(
            f"{record_id}: no complete monotonic token projection"
        )

    minimum_cost = min(cost for _, cost in complete)
    best_starts = [
        index for index, cost in complete if cost == minimum_cost
    ]
    total_best = min(
        2,
        sum(best_count[0][index] for index in best_starts),
    )
    if total_best > 1:
        raise SegmentationProjectionError(
            f"{record_id}: ambiguous minimum-cost monotonic token projection"
        )

    current = best_starts[0]
    result: list[_TokenMatch] = []
    for token_index, token_matches in enumerate(choices):
        result.append(token_matches[current])
        if token_index == len(tokens) - 1:
            break
        selected_index = best_next[token_index][current]
        if selected_index is None:
            raise SegmentationProjectionError(
                f"{record_id}: ambiguous projection while reconstructing "
                "minimum-cost token sequence"
            )
        current = selected_index
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
    if target is None:
        raise SegmentationProjectionError(
            f"{record_id}: selected segmentation has no target source edition"
        )
    primary = _primary_atoms(
        ir,
        primary_layer=primary_layer,
        target=target,
    )
    projectable_specs = tuple(spec for spec in specs if spec.atoms)
    embedding = _unique_embedding(
        primary,
        projectable_specs,
        record_id=record_id,
    )
    selected_candidate_key = candidate_keys[resolution.selected_index]
    embedding_index = 0

    def emit_annotations(
        spec: _TokenSpec,
        match: _TokenMatch | None,
    ) -> None:
        for annotation in spec.annotations:
            if annotation.start == annotation.end:
                ann_sign_keys: tuple[str, ...] = ()
            else:
                if match is None:
                    raise SegmentationProjectionError(
                        f"{record_id}: non-empty annotation in zero-atom token"
                    )
                mapped_positions = [
                    position
                    for position in match.positions[
                        annotation.start : annotation.end
                    ]
                    if position is not None
                ]
                if not mapped_positions:
                    ann_sign_keys = ()
                else:
                    ann_first = primary[mapped_positions[0]].sign_start
                    ann_last = primary[mapped_positions[-1]].sign_end
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

    for spec in specs:
        if not spec.atoms:
            emit_annotations(spec, None)
            continue

        match = embedding[embedding_index]
        embedding_index += 1
        first_sign = primary[match.start].sign_start
        last_sign = primary[match.end - 1].sign_end
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
            "segmentation_status": (
                "projected_with_source_drift"
                if match.drift_edits
                else "projected"
            ),
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
        emit_annotations(spec, match)

    if embedding_index != len(embedding):
        raise SegmentationProjectionError(
            f"{record_id}: internal projection accounting mismatch"
        )

    return InscriptionIR(
        identity=ir.identity,
        provenance=ir.provenance,
        signs=ir.signs,
        nodes=tuple(nodes),
        edges=tuple(dict.fromkeys(edges)),
        diagnostics=ir.diagnostics,
    )
