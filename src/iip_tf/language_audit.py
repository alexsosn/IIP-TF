"""Explain residual source-labelled Hebrew signs in Aramaic IIP transcriptions.

This module is an *audit*, not a language resolver: it never changes IR
or infers linguistic identity from script. Its mutually exclusive reason
buckets are intentionally conservative and test the source-backed
precedence promised by issue #54's existing language resolver.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from iip_tf.encoded_script import encoded_script
from iip_tf.ir import InscriptionIR, IRSign, Layer, NodeType

# Report labels describe reasons *not to correct automatically*, not proven
# mistakes. Source attribute provenance takes precedence over word guesses.
_LANGUAGE_UNKNOWN = "<untagged>"


def _paragraph_hebrew(sign: IRSign) -> bool:
    return (
        sign.lang_origin == "p"
        and sign.lang_original is not None
        and sign.lang_original.strip() == "heb"
    )


def _word_index(
    ir: InscriptionIR, relevant: set[str]
) -> dict[str, list[tuple[str, str]]]:
    """Selected, already projected word evidence on original canonical keys."""
    index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for node in ir.nodes:
        if (
            node.node_type != NodeType.WORD
            or node.feature("lang_source") != "transcription_segmented"
        ):
            continue
        status = node.feature("segmentation_status")
        value = node.feature("lang")
        status_text = status if isinstance(status, str) else "<unknown-status>"
        language = value if isinstance(value, str) and value else _LANGUAGE_UNKNOWN
        for key in node.sign_keys:
            if key in relevant:
                index[key].append((status_text, language))
    return index


def _reason(
    sign: IRSign, evidence: list[tuple[str, str]]
) -> str:
    """Exactly one explanation per source-valued transcription sign."""
    if sign.synthetic_kind is not None or not sign.glyph:
        return "synthetic"
    if not sign.glyph.isalpha():
        return "nonletter"
    if encoded_script(sign.glyph) != "Hebr":
        return "non_hebrew_encoded_letter"
    if sign.lang_origin != "p":
        return "non_paragraph_source"
    if sign.lang_original is None or sign.lang_original.strip() != "heb":
        return "source_label_not_heb"
    if not evidence:
        return "no_selected_word"
    if any(status != "projected" for status, _ in evidence):
        return "drift_or_uncertain_word_overlap"
    languages = {language for _, language in evidence}
    if "arc" in languages:
        if len(languages) != 1:
            raise ValueError(
                f"{sign.key}: conflicting selected arc language with {sorted(languages)}"
            )
        raise ValueError(f"{sign.key}: aligned clean arc word but sign still heb")
    if _LANGUAGE_UNKNOWN in languages:
        return "selected_word_without_lang"
    return "selected_non_arc_word"


@dataclass
class AramaicLanguageAudit:
    """Accumulate a deterministic source-backed corpus-level language inventory."""

    max_examples: int = 3
    records_scanned: int = 0
    corrected_signs: int = 0
    remaining_signs: int = 0
    _reasons: Counter[str] = field(default_factory=Counter)
    _remaining_by_record: Counter[str] = field(default_factory=Counter)
    _clean_word_languages: Counter[str] = field(default_factory=Counter)
    _examples: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_examples < 1:
            raise ValueError("max_examples must be positive")

    def ingest(self, ir: InscriptionIR) -> None:
        """Inspect resolved IR once; no text generation or mutations."""
        if ir.identity.main_lang != "arc":
            return
        self.records_scanned += 1
        relevant = {
            sign.key for sign in ir.signs
            if sign.layer == Layer.TRANSCRIPTION
            and (sign.lang == "heb" or sign.lang_source == "transcription_segmented")
        }
        words = _word_index(ir, relevant)
        for sign in ir.signs:
            if sign.layer != Layer.TRANSCRIPTION or sign.key not in relevant:
                continue
            evidence = words.get(sign.key, [])
            if sign.lang == "arc" and sign.lang_source == "transcription_segmented":
                # Independent check: an override must have been supported by
                # uncontested source words and authentic paragraph provenance.
                if (
                    not _paragraph_hebrew(sign)
                    or encoded_script(sign.glyph) != "Hebr"
                    or not evidence
                    or any(status != "projected" or lang != "arc"
                           for status, lang in evidence)
                ):
                    qualifier = (
                        "drift or uncertain overlap"
                        if any(status != "projected" for status, _ in evidence)
                        else "corrected without clean arc word/provenance"
                    )
                    raise ValueError(f"{sign.key}: {qualifier}")
                self.corrected_signs += 1
            if sign.lang != "heb":
                continue
            reason = _reason(sign, evidence)
            self.remaining_signs += 1
            self._reasons[reason] += 1
            self._remaining_by_record[ir.identity.inscription_id] += 1
            # One vote per sign/language, even if overlapping words repeat.
            self._clean_word_languages.update({
                lang for status, lang in evidence if status == "projected"
            })
            sample = {
                "record": ir.identity.inscription_id,
                "sign_key": sign.key,
                "glyph": sign.glyph,
                "lang_origin": sign.lang_origin or "",
                "lang_original": sign.lang_original or "",
                "aligned_word_evidence": ";".join(
                    f"{status}:{lang}" for status, lang in sorted(set(evidence))
                ),
            }
            bucket = self._examples.setdefault(reason, [])
            bucket.append(sample)
            bucket.sort(key=lambda s: (s["record"], s["sign_key"]))
            del bucket[self.max_examples:]

    def report(self) -> dict[str, Any]:
        """Stable, JSON-compatible counts and bounded examples."""
        if sum(self._reasons.values()) != self.remaining_signs:
            raise ValueError("unreconciled residual language bucket counts")
        return {
            "records_scanned": self.records_scanned,
            "corrected_signs": self.corrected_signs,
            "remaining_signs": self.remaining_signs,
            "reasons": dict(sorted(self._reasons.items())),
            "clean_word_languages_for_remaining": dict(
                sorted(self._clean_word_languages.items())
            ),
            "examples": {
                reason: [dict(item) for item in samples]
                for reason, samples in sorted(self._examples.items())
            },
            "records_with_remaining": len(self._remaining_by_record),
            "most_affected_records": [
                {"record": name, "remaining_signs": count}
                for name, count in sorted(
                    self._remaining_by_record.items(),
                    key=lambda item: (-item[1], item[0]),
                )[:10]
            ],
        }
