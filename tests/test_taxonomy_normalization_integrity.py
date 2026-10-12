"""Independent read-back integrity checks for source taxonomy normalization (#64).

These RED-first tests exercise actual node-feature maps independently of the
metadata IR transformer. The pinned source audit must validate BOTH surfaces.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from iip_tf.taxonomy_audit import (
    TaxonomyError,
    TaxonomyRegistry,
    validate_native_normalization,
)


class _Feature:
    def __init__(self, values: dict[int, str]) -> None:
        self.values = values

    def items(self) -> Any:
        return self.values.items()


def _registry() -> TaxonomyRegistry:
    return TaxonomyRegistry({
        "IIP-form": {"block": "Block"},
        "IIP-materials": {"clay": "Clay"},
        "IIP-genre": {"dedicatory": "Dedicatory"},
        "IIP-preservation": {"complete": "Complete"},
        "IIP-writing": {"painted": "Painted"},
        "IIP-religion": {"jewish": "Jewish", "pagan": "Pagan"},
    })


def _api(
    originals: dict[int, str],
    canonical: dict[int, str],
    *,
    inscriptions: tuple[int, ...] = (1, 2, 3, 4),
) -> Any:
    features = {
        "religion_original": _Feature(originals),
        "religion": _Feature(canonical),
    }
    for name in ("genre", "object_type", "material", "condition"):
        features[name] = _Feature({})
        features[name + "_original"] = _Feature({})
    return SimpleNamespace(
        F=SimpleNamespace(otype=SimpleNamespace(s=lambda name: inscriptions)),
        Fs=lambda name: features[name],
    )


def test_validates_every_canonical_value_against_verbatim_source() -> None:
    api = _api(
        {1: "#jewish", 2: "jewish\t#pagan #jewish", 3: "#jewish #missing",
         4: "#clay"},
        {1: "jewish", 2: "jewish pagan jewish"},
    )
    report = validate_native_normalization(api, _registry())
    assert report["normalized_fields"] == 2
    assert report["unresolved_fields"] == {"religion": 2}


@pytest.mark.parametrize(
    ("originals", "canonical"),
    [
        ({1: "#jewish"}, {1: "pagan"}),               # legal, but wrong ID
        ({1: "#jewish"}, {}),                          # silently lost valid ID
        ({1: "#jewish #missing"}, {1: "jewish"}),      # partial mapping
        ({1: "#clay"}, {1: "clay"}),                    # wrong taxonomy
        ({1: "Jewish"}, {1: "jewish"}),                 # fuzzy case matching
        ({1: "#jewish"}, {1: "#jewish"}),              # kept leading ref marker
        ({}, {1: "jewish"}),                           # fabricated missing source
    ],
)
def test_rejects_corruption_even_when_source_inventory_is_unchanged(
    originals: dict[int, str], canonical: dict[int, str],
) -> None:
    with pytest.raises(TaxonomyError):
        validate_native_normalization(_api(originals, canonical), _registry())


@pytest.mark.parametrize(
    ("originals", "canonical"),
    [
        ({5: "#jewish"}, {5: "jewish"}),
        ({1: "#jewish"}, {1: "jewish", 5: "jewish"}),
    ],
)
def test_rejects_classifications_outside_inscription_nodes(
    originals: dict[int, str], canonical: dict[int, str],
) -> None:
    with pytest.raises(TaxonomyError, match="inscription"):
        validate_native_normalization(_api(originals, canonical), _registry())


def test_rejects_ambiguous_duplicate_source_ids_even_if_report_is_consistent() -> None:
    # Repetition is meaningful source order; never collapse repeated tokens.
    api = _api({1: "#jewish jewish"}, {1: "jewish"})
    with pytest.raises(TaxonomyError):
        validate_native_normalization(api, _registry())
