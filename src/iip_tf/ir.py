"""Typed canonical intermediate representation for IIP-TF."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TypeAlias

FeatureValue: TypeAlias = str | int


class Layer(StrEnum):
    TRANSCRIPTION = "transcription"
    DIPLOMATIC = "diplomatic"
    TRANSLATION = "translation"
    COMMENTARY = "commentary"
    ANCHOR = "anchor"


class NodeType(StrEnum):
    INSCRIPTION = "inscription"
    EDITION = "edition"
    TEXTPART = "textpart"
    PARAGRAPH = "paragraph"
    LINE = "line"
    MARKUP = "markup"
    ENTITY = "entity"
    BIBL = "bibl"
    BIBL_SCOPE = "bibl_scope"
    HAND = "hand"
    DECORATION = "decoration"
    IMAGE = "image"
    REVISION = "revision"
    DIMENSION = "dimension"
    SUPPORT_NOTE = "support_note"
    FACSIMILE_SURFACE = "facsimile_surface"
    WORD = "word"
    SEGMENTATION = "segmentation"


class EdgeType(StrEnum):
    PARENT = "parent"
    IN_INSCRIPTION = "in_inscription"
    CORRESPONDS_TO = "corresponds_to"
    CITES = "cites"
    SEGMENTATION_OF = "segmentation_of"
    TOKEN_FROM = "token_from"


@dataclass(frozen=True)
class SourceIdentity:
    inscription_id: str
    source_file: str
    xml_id: str | None
    iip_ids: tuple[str, ...]
    main_lang: str | None


@dataclass(frozen=True)
class SourceProvenance:
    source_revision: str
    repaired: bool
    repair_id: str | None
    conflict_count: int


@dataclass(frozen=True)
class IRSign:
    key: str
    glyph: str
    layer: Layer
    lang: str | None = None
    lang_source: str = "none"
    reading_role: str = "both"
    synthetic_kind: str | None = None
    after: str = ""

    def __post_init__(self) -> None:
        if self.glyph and self.synthetic_kind is not None:
            raise ValueError(f"{self.key}: visible sign cannot also be synthetic")
        if len(self.glyph) > 1:
            raise ValueError(f"{self.key}: visible sign must contain one Unicode code point")
        if self.reading_role not in {"both", "normalized", "source"}:
            raise ValueError(f"{self.key}: invalid reading role {self.reading_role!r}")


@dataclass(frozen=True)
class IRNode:
    key: str
    node_type: NodeType
    sign_keys: tuple[str, ...]
    features: tuple[tuple[str, FeatureValue], ...] = ()
    point_index: int | None = None

    def feature(self, name: str) -> FeatureValue | None:
        for feature_name, value in self.features:
            if feature_name == name:
                return value
        return None

    @property
    def feature_map(self) -> MappingProxyType[str, FeatureValue]:
        return MappingProxyType(dict(self.features))


@dataclass(frozen=True)
class IREdge:
    edge_type: EdgeType
    source: str
    target: str


@dataclass(frozen=True)
class IRDiagnostic:
    code: str
    severity: str
    message: str
    source_key: str | None = None


@dataclass(frozen=True)
class InscriptionIR:
    identity: SourceIdentity
    provenance: SourceProvenance
    signs: tuple[IRSign, ...]
    nodes: tuple[IRNode, ...]
    edges: tuple[IREdge, ...]
    diagnostics: tuple[IRDiagnostic, ...]

    def __post_init__(self) -> None:
        sign_keys = [sign.key for sign in self.signs]
        if len(sign_keys) != len(set(sign_keys)):
            raise ValueError("duplicate sign key")

        node_keys = [node.key for node in self.nodes]
        if len(node_keys) != len(set(node_keys)):
            raise ValueError("duplicate node key")

        all_keys = set(sign_keys) | set(node_keys)
        for node in self.nodes:
            missing = set(node.sign_keys) - set(sign_keys)
            if missing:
                raise ValueError(f"{node.key}: unknown sign keys {sorted(missing)!r}")
            if node.point_index is not None:
                if node.sign_keys:
                    raise ValueError(
                        f"{node.key}: point_index requires an empty semantic span"
                    )
                if not 0 <= node.point_index <= len(self.signs):
                    raise ValueError(
                        f"{node.key}: point_index {node.point_index} outside "
                        f"0..{len(self.signs)}"
                    )

        for edge in self.edges:
            if edge.source not in all_keys or edge.target not in all_keys:
                raise ValueError(
                    f"unknown edge endpoint: {edge.edge_type.value} "
                    f"{edge.source!r} -> {edge.target!r}"
                )

    def sign(self, key: str) -> IRSign:
        for sign in self.signs:
            if sign.key == key:
                return sign
        raise KeyError(key)

    def node(self, key: str) -> IRNode:
        for node in self.nodes:
            if node.key == key:
                return node
        raise KeyError(key)

    def nodes_of_type(self, node_type: NodeType) -> tuple[IRNode, ...]:
        return tuple(node for node in self.nodes if node.node_type == node_type)

    def node_feature(self, node_type: NodeType, feature: str) -> FeatureValue | None:
        nodes = self.nodes_of_type(node_type)
        if len(nodes) != 1:
            raise ValueError(
                f"expected one {node_type.value} node, found {len(nodes)}"
            )
        return nodes[0].feature(feature)

    def text(self, sign_keys: tuple[str, ...] | list[str]) -> str:
        wanted = set(sign_keys)
        parts: list[str] = []
        for index, sign in enumerate(self.signs):
            if sign.key not in wanted:
                continue
            parts.append(sign.glyph)
            if (
                sign.after
                and index + 1 < len(self.signs)
                and self.signs[index + 1].key in wanted
            ):
                parts.append(sign.after)
        return "".join(parts)
