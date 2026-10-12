"""RED-first regression checks for complete CF feature and edge fingerprints."""

from __future__ import annotations

import pytest

from scripts.validate_pinned_context_fabric import (
    ParityError,
    compare_manifests,
    fingerprint_rows,
)


def test_node_fingerprint_detects_value_changes_and_missingness() -> None:
    baseline = fingerprint_rows([(1, "α"), (3, ""), (4, 0)], kind="node")
    assert baseline == fingerprint_rows([(1, "α"), (3, ""), (4, 0)], kind="node")
    assert baseline != fingerprint_rows([(1, "α"), (3, ""), (4, "0")], kind="node")
    assert baseline != fingerprint_rows([(1, "α"), (3, None), (4, 0)], kind="node")
    assert baseline != fingerprint_rows([(1, "α"), (2, ""), (4, 0)], kind="node")


def test_edge_fingerprint_distinguishes_target_sets_and_values() -> None:
    pairs = [(4, {1, 3}), (5, {3})]
    assert fingerprint_rows(pairs, kind="edge") == fingerprint_rows(
        [(4, {3, 1}), (5, {3})], kind="edge"
    )
    assert fingerprint_rows(pairs, kind="edge") != fingerprint_rows(
        [(4, {1, 2}), (5, {3})], kind="edge"
    )
    valued = fingerprint_rows([(4, {1: 0, 3: None})], kind="edge")
    assert valued != fingerprint_rows([(4, {1: 1, 3: None})], kind="edge")
    assert valued != fingerprint_rows([(4, {1, 3})], kind="edge")


def test_empty_features_are_recorded_not_dropped() -> None:
    assert fingerprint_rows([], kind="node")["count"] == 0
    assert fingerprint_rows([], kind="edge")["count"] == 0


def test_noncanonical_row_order_fails_closed() -> None:
    with pytest.raises(ParityError, match="order"):
        fingerprint_rows([(3, "a"), (1, "b")], kind="node")


def test_feature_inventory_and_values_must_match() -> None:
    native = {
        "slot_type": "sign",
        "max_slot": 2,
        "max_node": 4,
        "features": {"node:glyph": {"count": 2, "sha256": "abc"}},
    }
    compare_manifests(native, dict(native))
    with pytest.raises(ParityError, match="node:glyph"):
        compare_manifests(
            native, {**native, "features": {"node:glyph": {"count": 2, "sha256": "def"}}}
        )
    with pytest.raises(ParityError, match="inventory"):
        compare_manifests(native, {**native, "features": {}})
