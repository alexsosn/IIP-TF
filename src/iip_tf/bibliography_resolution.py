"""Exact source-faithful lookup of inscription bibliography pointer targets.

No authority graph is created here. A target is never silently corrected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from iip_tf.bibliography_index import BibliographyEntry, BibliographyIndex

_REASON = Literal["missing", "malformed", "unknown_key"]
_TARGET = re.compile(r"(IIP-[0-9]+)(?:\.xml)?")


@dataclass(frozen=True)
class BibliographyResolution:
    target: str | None
    key: str | None
    entry: BibliographyEntry | None
    reason: _REASON | None


def resolve_bibliography_target(
    index: BibliographyIndex,
    target: str | None,
) -> BibliographyResolution:
    """Resolve an exact IIP pointer only when its authority key is attested.

    The raw target remains untouched. Multiple explicitly attested keys can
    identify one TEI work, but no implicit aliasing or zero-padding is applied.
    """
    if target is None or target == "":
        return BibliographyResolution(target, None, None, "missing")
    match = _TARGET.fullmatch(target)
    if match is None:
        return BibliographyResolution(target, None, None, "malformed")
    key = match.group(1)
    entry = index.by_key.get(key)
    if entry is None:
        return BibliographyResolution(target, None, None, "unknown_key")
    return BibliographyResolution(target, key, entry, None)
