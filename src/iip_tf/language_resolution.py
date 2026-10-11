"""Source-backed, deliberately narrow sign-language precedence for IIP #54.

Only an explicitly projected source word may supersede a paragraph's
script-like xml:lang=heb for Hebrew-encoded letters of Aramaic transcription.
This must never infer language from Unicode script alone.
"""

from __future__ import annotations

from dataclasses import replace

from iip_tf.encoded_script import encoded_script
from iip_tf.ir import InscriptionIR, IRSign, Layer, NodeType


class LanguageResolutionError(ValueError):
    """Selected segmented tokens assign incompatible languages to one sign."""


def _eligible(sign: IRSign) -> bool:
    return (
        sign.layer == Layer.TRANSCRIPTION
        and sign.lang == "heb"
        and sign.lang_source in {"xml:lang", "inherited"}
        and sign.lang_original is not None
        and sign.lang_original.strip() == "heb"
        and sign.lang_origin == "p"
        and encoded_script(sign.glyph) == "Hebr"
    )


def resolve_sign_languages(ir: InscriptionIR) -> InscriptionIR:
    """Apply verified segmented Aramaic words only to script-like paragraph signs.

    Unsegmented/unknown/drifted words, synthetic slots, non-Aramaic records,
    diplomatic and translation layers, explicit foreign spans and unsupported
    scripts all retain their source-valued language. Conflicting projected
    token evidence fails closed rather than choosing an arbitrary winner.
    """
    if ir.identity.main_lang != "arc":
        return ir

    candidates = {sign.key for sign in ir.signs if _eligible(sign)}
    if not candidates:
        return ir

    observed: dict[str, set[str]] = {}
    for word in ir.nodes_of_type(NodeType.WORD):
        if (
            word.feature("lang_source") != "transcription_segmented"
            or word.feature("segmentation_status") != "projected"
        ):
            continue
        lang = word.feature("lang")
        for key in word.sign_keys:
            if key not in candidates:
                continue
            # Unknown explicitly projected tokens block inference; they do
            # not manufacture a target language for overlapping signs.
            observed.setdefault(key, set()).add(
                lang if isinstance(lang, str) and lang else "<unspecified>"
            )

    new_signs: list[IRSign] = []
    for sign in ir.signs:
        langs = observed.get(sign.key, set())
        if len(langs) > 1:
            raise LanguageResolutionError(
                f"{ir.identity.inscription_id}: conflicting selected word "
                f"languages for {sign.key}: {sorted(langs)!r}"
            )
        if langs == {"arc"}:
            # lang_original and lang_origin continue to describe the original
            # source paragraph, not the selected word that won precedence.
            new_signs.append(
                replace(sign, lang="arc", lang_source="transcription_segmented")
            )
        else:
            new_signs.append(sign)

    return replace(ir, signs=tuple(new_signs))
