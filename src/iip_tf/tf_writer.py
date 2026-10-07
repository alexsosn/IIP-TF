"""Deterministic native Text-Fabric serialization of canonical IIP-TF IR."""

from __future__ import annotations

import shutil
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf import __version__
from iip_tf.ir import IRNode, IRSign, InscriptionIR, Layer, NodeType

_NODE_TYPE_ORDER = (
    NodeType.INSCRIPTION,
    NodeType.EDITION,
    NodeType.TEXTPART,
    NodeType.LINE,
    NodeType.WORD,
    NodeType.MARKUP,
    NodeType.ENTITY,
    NodeType.SEGMENTATION,
    NodeType.BIBL,
    NodeType.HAND,
    NodeType.DECORATION,
    NodeType.IMAGE,
    NodeType.REVISION,
    NodeType.PARAGRAPH,
    NodeType.BIBL_SCOPE,
    NodeType.DIMENSION,
    NodeType.SUPPORT_NOTE,
    NodeType.FACSIMILE_SURFACE,
)
_NODE_TYPE_RANK = {node_type: index for index, node_type in enumerate(_NODE_TYPE_ORDER)}
_INT_FEATURES = {
    "line_n",
    "quantity_int",
    "date_not_before_int",
    "date_not_after_int",
    "point_index",
}
_EMPTY_STRUCTURAL_TYPES = {NodeType.EDITION, NodeType.PARAGRAPH}

_SOURCE_NAME = "Inscriptions of Israel/Palestine, Brown University"
_SOURCE_URL = "https://github.com/Brown-University-Library/iip-texts"
_SOURCE_DOI = "10.26300/pz1d-st89"
_DATA_LICENSE = "CC BY-NC 4.0"
_DATA_LICENSE_URL = "https://creativecommons.org/licenses/by-nc/4.0/"


class TFWriterError(RuntimeError):
    """Raised when canonical IR cannot be serialized without semantic loss."""


def _set_feature(
    features: dict[str, dict[int, str | int]],
    name: str,
    node: int,
    value: str | int | None,
) -> None:
    if value is None or value == "":
        return
    existing = features[name].get(node)
    if existing is not None and existing != value:
        raise TFWriterError(
            f"conflicting feature {name!r} on TF node {node}: "
            f"{existing!r} vs {value!r}"
        )
    features[name][node] = value


def _primary_layer(ir: InscriptionIR) -> str:
    value = ir.node_feature(NodeType.INSCRIPTION, "primary_layer")
    if not isinstance(value, str):
        raise TFWriterError(
            f"{ir.identity.inscription_id}: inscription lacks string primary_layer"
        )
    return value


def _record_anchor_key(ir: InscriptionIR) -> str:
    primary = _primary_layer(ir)
    if primary == "empty":
        candidates = [
            sign.key for sign in ir.signs if sign.synthetic_kind == "anchor"
        ]
    else:
        candidates = [
            sign.key for sign in ir.signs if sign.layer.value == primary
        ]
    if not candidates:
        raise TFWriterError(
            f"{ir.identity.inscription_id}: no technical anchor for primary layer {primary!r}"
        )
    return candidates[0]


def _view(
    signs: tuple[IRSign, ...],
    include: Callable[[IRSign], bool],
) -> tuple[dict[str, str], dict[str, str]]:
    selected = [include(sign) for sign in signs]
    glyphs: dict[str, str] = {}
    afters: dict[str, str] = {}

    for index, sign in enumerate(signs):
        if selected[index] and sign.glyph:
            glyphs[sign.key] = sign.glyph
        if selected[index] and sign.after:
            afters[sign.key] = sign.after

    for index, sign in enumerate(signs):
        if selected[index] or not sign.after:
            continue
        previous: int | None = None
        for candidate in range(index - 1, -1, -1):
            if signs[candidate].layer != sign.layer:
                break
            if selected[candidate]:
                previous = candidate
                break
        if previous is None:
            continue
        has_later_selected = False
        for candidate in range(index + 1, len(signs)):
            if signs[candidate].layer != sign.layer:
                break
            if selected[candidate]:
                has_later_selected = True
                break
        if has_later_selected and not afters.get(signs[previous].key):
            afters[signs[previous].key] = sign.after

    return glyphs, afters


def _add_view_features(
    features: dict[str, dict[int, str | int]],
    *,
    ir: InscriptionIR,
    slot_by_key: dict[str, int],
) -> None:
    primary = _primary_layer(ir)
    views: dict[str, tuple[dict[str, str], dict[str, str]]] = {
        "primary": _view(
            ir.signs,
            lambda sign: sign.layer.value == primary
            and sign.reading_role in {"both", "normalized"},
        ),
        "source": _view(
            ir.signs,
            lambda sign: sign.layer.value == primary
            and sign.reading_role in {"both", "source"},
        ),
    }
    for layer in (
        Layer.TRANSCRIPTION,
        Layer.DIPLOMATIC,
        Layer.TRANSLATION,
        Layer.COMMENTARY,
    ):
        views[layer.value] = _view(
            ir.signs,
            lambda sign, layer=layer: sign.layer == layer
            and sign.reading_role in {"both", "normalized"},
        )

    for prefix, (glyphs, afters) in views.items():
        for key, value in glyphs.items():
            _set_feature(features, f"{prefix}_glyph", slot_by_key[key], value)
        for key, value in afters.items():
            _set_feature(features, f"{prefix}_after", slot_by_key[key], value)


def _feature_metadata(
    node_features: dict[str, dict[int, str | int]],
    edge_features: dict[str, dict[int, set[int]]],
    generic: dict[str, str],
) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {"": generic}
    for name, values in node_features.items():
        expected = int if name in _INT_FEATURES else str
        wrong = sorted(
            node
            for node, value in values.items()
            if type(value) is not expected
        )
        if wrong:
            raise TFWriterError(
                f"feature {name!r} has values outside declared "
                f"{'int' if expected is int else 'str'} domain at nodes {wrong[:8]!r}"
            )
        metadata[name] = {"valueType": "int" if expected is int else "str"}
    for name in edge_features:
        metadata[name] = {"valueType": "str"}
    return metadata


def _otext() -> dict[str, str]:
    return {
        "sectionTypes": "inscription,textpart,line",
        "sectionFeatures": "inscription_id,section_part,line_n",
        "fmt:text-orig-full": "{primary_glyph}{primary_after}",
        "fmt:text-layer-full": "{glyph}{after}",
        "fmt:text-source-full": "{source_glyph}{source_after}",
        "fmt:text-transcription-full": "{transcription_glyph}{transcription_after}",
        "fmt:text-diplomatic-full": "{diplomatic_glyph}{diplomatic_after}",
        "fmt:text-translation-full": "{translation_glyph}{translation_after}",
        "fmt:text-commentary-full": "{commentary_glyph}{commentary_after}",
        "fmt:word-default": "{word_text}",
    }


def _normalize_headers(output_dir: Path) -> None:
    for path in sorted(output_dir.glob("*.tf")):
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        normalized = [line for line in lines if not line.startswith("@dateWritten=")]
        path.write_text("".join(normalized), encoding="utf-8")


def _clear_binary_cache(output_dir: Path) -> None:
    shutil.rmtree(output_dir / ".tf", ignore_errors=True)


def write_tf_corpus(
    irs: Iterable[InscriptionIR],
    output_dir: Path,
    *,
    converter_commit: str,
) -> None:
    """Write canonical IR records as deterministic Text-Fabric feature files."""

    records = tuple(sorted(irs, key=lambda ir: ir.identity.inscription_id))
    if not records:
        raise TFWriterError("cannot write an empty corpus")
    if not converter_commit:
        raise TFWriterError("converter_commit must be non-empty")

    record_ids = [ir.identity.inscription_id for ir in records]
    if len(record_ids) != len(set(record_ids)):
        raise TFWriterError("duplicate canonical inscription_id")

    revisions = {ir.provenance.source_revision for ir in records}
    if len(revisions) != 1:
        raise TFWriterError(f"inconsistent source revision values: {sorted(revisions)!r}")
    source_revision = next(iter(revisions))

    slot_by_key: dict[str, int] = {}
    owner_by_key: dict[str, InscriptionIR] = {}
    next_slot = 1
    for ir in records:
        for sign in ir.signs:
            if sign.key in owner_by_key:
                raise TFWriterError(f"duplicate canonical key {sign.key!r}")
            slot_by_key[sign.key] = next_slot
            owner_by_key[sign.key] = ir
            next_slot += 1
        for node in ir.nodes:
            if node.key in owner_by_key:
                raise TFWriterError(f"duplicate canonical key {node.key!r}")
            owner_by_key[node.key] = ir

    max_slot = next_slot - 1
    ordered_nodes = sorted(
        (
            (ir, node)
            for ir in records
            for node in ir.nodes
        ),
        key=lambda item: (
            _NODE_TYPE_RANK[item[1].node_type],
            item[0].identity.inscription_id,
            item[1].key,
        ),
    )

    node_by_key: dict[str, int] = {}
    otype: dict[int, str] = {
        slot: "sign" for slot in range(1, max_slot + 1)
    }
    for offset, (_, node) in enumerate(ordered_nodes, start=max_slot + 1):
        node_by_key[node.key] = offset
        otype[offset] = node.node_type.value

    key_to_tf = {**slot_by_key, **node_by_key}
    node_features: dict[str, dict[int, str | int]] = defaultdict(dict)
    node_features["otype"] = otype
    edge_features: dict[str, dict[int, set[int]]] = defaultdict(dict)
    oslots: dict[int, set[int]] = {}

    for ir in records:
        for sign in ir.signs:
            slot = slot_by_key[sign.key]
            _set_feature(node_features, "glyph", slot, sign.glyph)
            _set_feature(node_features, "after", slot, sign.after)
            _set_feature(node_features, "layer", slot, sign.layer.value)
            _set_feature(node_features, "lang", slot, sign.lang)
            _set_feature(node_features, "lang_source", slot, sign.lang_source)
            _set_feature(node_features, "reading_role", slot, sign.reading_role)
            _set_feature(node_features, "synthetic_kind", slot, sign.synthetic_kind)
        _add_view_features(node_features, ir=ir, slot_by_key=slot_by_key)

    for ir, node in ordered_nodes:
        tf_node = node_by_key[node.key]
        seen_names: set[str] = set()
        for name, value in node.features:
            if name in seen_names:
                raise TFWriterError(f"{node.key}: duplicate feature {name!r}")
            seen_names.add(name)
            _set_feature(node_features, name, tf_node, value)

        if node.sign_keys:
            slots = {slot_by_key[key] for key in node.sign_keys}
        elif node.point_index is not None:
            record_slots = [slot_by_key[sign.key] for sign in ir.signs]
            if node.point_index < len(record_slots):
                anchor = record_slots[node.point_index]
                relation = "before"
                reconstructed = record_slots.index(anchor)
            else:
                anchor = record_slots[-1]
                relation = "after"
                reconstructed = record_slots.index(anchor) + 1
            if reconstructed != node.point_index:
                raise TFWriterError(
                    f"{node.key}: point anchor does not reconstruct point_index"
                )
            slots = {anchor}
            _set_feature(node_features, "point_index", tf_node, node.point_index)
            _set_feature(node_features, "point_relation", tf_node, relation)
        else:
            if node.node_type not in _EMPTY_STRUCTURAL_TYPES:
                raise TFWriterError(
                    f"{node.key}: empty semantic span has no supported technical anchor"
                )
            anchor = slot_by_key[_record_anchor_key(ir)]
            slots = {anchor}
            existing_empty = node.feature("empty")
            if existing_empty not in {None, "1"}:
                raise TFWriterError(
                    f"{node.key}: empty structural node has empty={existing_empty!r}"
                )
            _set_feature(node_features, "empty", tf_node, "1")
        if not slots:
            raise TFWriterError(f"{node.key}: non-slot node has empty oslots")
        oslots[tf_node] = slots

    edge_features["oslots"] = oslots
    for ir in records:
        for edge in ir.edges:
            source = key_to_tf.get(edge.source)
            target = key_to_tf.get(edge.target)
            if source is None or target is None:
                raise TFWriterError(
                    f"{ir.identity.inscription_id}: unknown edge endpoint "
                    f"{edge.source!r} -> {edge.target!r}"
                )
            feature = edge_features[edge.edge_type.value]
            feature.setdefault(source, set()).add(target)

    generic = {
        "source": _SOURCE_NAME,
        "sourceUrl": _SOURCE_URL,
        "sourceCommit": source_revision,
        "sourceDOI": _SOURCE_DOI,
        "license": _DATA_LICENSE,
        "licenseUrl": _DATA_LICENSE_URL,
        "converterVersion": __version__,
        "converterCommit": converter_commit,
        "schemaVersion": "0.1",
    }
    metadata = _feature_metadata(node_features, edge_features, generic)
    metadata["otext"] = _otext()

    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.tf"):
        old.unlink()
    _clear_binary_cache(output_dir)

    tf = Fabric(locations=str(output_dir), silent=True)
    good = tf.save(
        nodeFeatures=dict(node_features),
        edgeFeatures=dict(edge_features),
        metaData=metadata,
        silent=True,
    )
    if not good:
        raise TFWriterError("Text-Fabric rejected generated feature data")

    _normalize_headers(output_dir)

    api: Any = Fabric(locations=str(output_dir), silent=True).loadAll(silent=True)
    if not api:
        raise TFWriterError("Text-Fabric could not reload generated corpus")

    for ir, node in ordered_nodes:
        if node.point_index is None:
            continue
        tf_node = node_by_key[node.key]
        loaded_slots = tuple(api.L.d(tf_node, otype="sign"))
        expected_slots = tuple(sorted(oslots[tf_node]))
        if loaded_slots != expected_slots:
            raise TFWriterError(f"{node.key}: point oslots changed after TF reload")
        if api.F.point_index.v(tf_node) != node.point_index:
            raise TFWriterError(f"{node.key}: point_index changed after TF reload")
        relation = api.F.point_relation.v(tf_node)
        expected_relation = "before" if node.point_index < len(ir.signs) else "after"
        if relation != expected_relation:
            raise TFWriterError(f"{node.key}: point_relation changed after TF reload")

    _clear_binary_cache(output_dir)
