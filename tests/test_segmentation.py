from __future__ import annotations

from pathlib import Path

import pytest
from iip_tf.segmentation import (
    PINNED_IIP_REVISION,
    SegmentationConflictError,
    resolve_segmented_editions,
)

FIXTURES = Path(__file__).parent / "fixtures" / "segmented_duplicates"


def test_ashk0016_selects_only_nonempty_candidate() -> None:
    result = resolve_segmented_editions(
        FIXTURES / "ashk0016.xml",
        source_revision=PINNED_IIP_REVISION,
    )

    assert result.selected_index == 1
    assert result.status == "sole_nonempty"
    assert result.suppressed_indices == (0,)
    assert result.source_changes == ("c2022-03-29", "c2023-07-10")
    assert result.conflict_fields == ()


def test_suhm0001_collapses_semantically_equivalent_rerun() -> None:
    result = resolve_segmented_editions(
        FIXTURES / "suhm0001.xml",
        source_revision=PINNED_IIP_REVISION,
    )

    assert result.selected_index == 0
    assert result.status == "equivalent_duplicates"
    assert result.suppressed_indices == (1,)
    assert result.source_changes == ("c2021-06-16", "c2023-07-10")
    assert result.conflict_fields == ()


def test_zoor0453_uses_validated_pinned_source_override() -> None:
    result = resolve_segmented_editions(
        FIXTURES / "zoor0453.xml",
        source_revision=PINNED_IIP_REVISION,
    )

    assert result.selected_index == 0
    assert result.status == "source_history_override"
    assert result.suppressed_indices == (1,)
    assert result.source_changes == ("c2021-06-16", "c2022-03-29")
    assert result.conflict_fields == ("xml:lang",)


def test_unknown_semantic_duplicate_conflict_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "unknown.xml"
    path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="unknown"><text><body>
<div type="edition" subtype="transcription_segmented" change="c2024-01-01">
  <p><w xml:id="unknown-1" xml:lang="grc">Α</w></p>
</div>
<div type="edition" subtype="transcription_segmented" change="c2024-02-01">
  <p><w xml:id="unknown-1" xml:lang="grc">Β</w></p>
</div>
</body></text></TEI>""",
        encoding="utf-8",
    )

    with pytest.raises(SegmentationConflictError, match="unknown"):
        resolve_segmented_editions(path, source_revision=PINNED_IIP_REVISION)


def test_zoor_override_refuses_changed_conflict_shape(tmp_path: Path) -> None:
    source = (FIXTURES / "zoor0453.xml").read_text(encoding="utf-8")
    changed = source.replace(
        '<w xml:id="zoor0453-1" xml:lang="grc">תתניח</w>',
        '<w xml:id="zoor0453-1" xml:lang="grc">DIFFERENT</w>',
    )
    path = tmp_path / "zoor0453.xml"
    path.write_text(changed, encoding="utf-8")

    with pytest.raises(SegmentationConflictError, match="override"):
        resolve_segmented_editions(path, source_revision=PINNED_IIP_REVISION)
