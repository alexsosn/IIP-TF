"""Pinned full-corpus native Text-Fabric validation for issue #5."""

from __future__ import annotations

import argparse
import gc
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from tf.fabric import Fabric  # type: ignore[import-untyped]

from iip_tf.ir import NodeType
from iip_tf.language_audit import AramaicLanguageAudit
from iip_tf.person_register import (
    PINNED_PERSONS_BLOB,
    attach_person_register,
    read_person_register,
)
from iip_tf.release_gate import (
    PINNED_EPIDOC_SOURCE_TREE,
    compare_tf_feature_hashes,
    inventory_source_files,
    require_empty_output_directory,
    require_source_tree_sha,
    validate_oslots_mapping,
    write_build_reports,
)
from iip_tf.text_parser import parse_epidoc_file
from iip_tf.tf_writer import write_tf_corpus

EXPECTED_PARSED = 5535
EXPECTED_SIGNS = 1466387
EXPECTED_NODES = 322860
EXPECTED_EDGES = 409785
EXPECTED_POINTS = 49
EXPECTED_EMPTY_STRUCTURAL = 11427
EXPECTED_SEGMENTED_TOKEN_IDENTITIES = 39472



def _validate_native_metadata_queries(api: Any) -> dict[str, int]:
    """Exercise native metadata node ownership and feature lookups on real IIP TF."""

    F, E = api.F, api.E
    checks = {
        "bibl_scope": ("bibl",),
        "dimension": ("inscription", "hand"),
        "facsimile_surface": ("inscription", "facsimile_surface"),
        "image": ("inscription", "facsimile_surface"),
        "support_note": ("inscription",),
        "revision": ("inscription",),
        "decoration": ("inscription",),
        "responsibility": ("inscription",),
        "publication_id": ("inscription",),
        "publication_include": ("inscription",),
        "publication_availability": ("inscription",),
        "publication_licence": ("publication_availability",),
        "publication_paragraph": ("publication_licence",),
        "publication_reference": ("publication_licence", "publication_paragraph"),
    }
    for node_type, allowed_parents in checks.items():
        nodes = F.otype.s(node_type)
        if not nodes:
            raise SystemExit(f"native metadata is missing {node_type} nodes")
        for node in nodes:
            parents = E.parent.f(node)
            if len(parents) != 1 or F.otype.v(parents[0]) not in allowed_parents:
                raise SystemExit(
                    f"{node_type} {node}: invalid direct parent {parents!r}"
                )

    # Every citation target must remain a queryable native bibliographic node.
    citations = 0
    for source, targets in E.cites.items():
        if F.otype.v(source) == "sign":
            raise SystemExit(f"cites edge originates from slot {source}")
        for target in targets:
            if F.otype.v(target) != "bibl":
                raise SystemExit(f"cites edge has non-bibl target {target}")
            citations += 1
    if not citations:
        raise SystemExit("no native citations are queryable")

    dated = tuple(api.Fs("date_not_before_int").items())
    if not dated or not any(
        isinstance(year, int) and isinstance(api.Fs("date_not_before").v(n), str)
        for n, year in dated
    ):
        raise SystemExit("raw/typed date features are not jointly queryable")

    referenced_places = tuple(api.Fs("settlement_ref").items())
    if not referenced_places or not all(
        F.otype.v(n) == "inscription" and isinstance(ref, str)
        for n, ref in referenced_places
    ):
        raise SystemExit("inscription settlement references are not queryable")

    nested_surfaces = sum(
        1
        for node in F.otype.s("facsimile_surface")
        if F.otype.v(E.parent.f(node)[0]) == "facsimile_surface"
    )
    if not nested_surfaces:
        raise SystemExit("nested facsimile surfaces lost on serialization")

    # Provenance must be source-explicit: XInclude does not confer authority.
    inscriptions = F.otype.s("inscription")
    responsibilities = F.otype.s("responsibility")
    includes = F.otype.s("publication_include")
    authorities = tuple(api.Fs("publication_authority").items())
    titles = tuple(api.Fs("source_title").items())
    if len(titles) != len(inscriptions) or len(responsibilities) != 5537:
        raise SystemExit("source titles/responsibility cardinality mismatch")
    if len(includes) != 3483 or len(authorities) != 2052:
        raise SystemExit("publication include/authority cardinality mismatch")
    if len(F.otype.s("publication_id")) != len(inscriptions):
        raise SystemExit("publication IDs are missing or duplicated")
    if len(F.otype.s("publication_availability")) != 3:
        raise SystemExit("explicit availability statements were not retained")
    if len(F.otype.s("publication_licence")) != 3:
        raise SystemExit("explicit licence declarations were not retained")
    if len(F.otype.s("publication_paragraph")) != 3:
        raise SystemExit("explicit licence paragraph nodes were not retained")
    if len(F.otype.s("publication_reference")) != 6:
        raise SystemExit("explicit licence reference nodes were not retained")
    source_include = (
        "http://cds.library.brown.edu/projects/iip/include_publicationStmt.xml"
    )
    for node in includes:
        if (
            F.include_href.v(node) != source_include
            or F.include_resolved.v(node) != "0"
            or not F.include_fallback_text.v(node)
        ):
            raise SystemExit(f"publication include {node}: invalid source pointer")
        owner = E.parent.f(node)[0]
        if F.publication_authority.v(owner) is not None:
            raise SystemExit(f"publication include {node}: invented explicit authority")
    for node in responsibilities:
        if (
            not F.agent_name.v(node)
            or F.agent_tag.v(node) not in {"name", "persName"}
        ):
            raise SystemExit(f"responsibility {node}: source agent was lost")
    role_ids = tuple(api.Fs("responsibility_role_source_id").items())
    if len(role_ids) != 579 or not all(
        F.otype.v(node) == "responsibility"
        and F.responsibility_construct.v(node) == "respStmt"
        and isinstance(source_id, str)
        and source_id
        for node, source_id in role_ids
    ):
        raise SystemExit(
            "source resp/@xml:id provenance count or type changed"
        )
    if sum(
        F.responsibility_construct.v(node) == "principal"
        for node in responsibilities
    ) != 1:
        raise SystemExit("source-specific principal record was not preserved")
    if sum(
        F.responsibility_role.v(node) == "Prinicipal Investigator"
        for node in responsibilities
    ) != 3445:
        raise SystemExit("original misspelled investigator roles were normalized away")

    return {
        "validated_responsibilities": len(responsibilities),
        "validated_responsibility_role_ids": len(role_ids),
        "validated_publication_ids": len(F.otype.s("publication_id")),
        "validated_unexpanded_includes": len(includes),
        "validated_explicit_publication_authorities": len(authorities),
        "validated_explicit_licences": len(F.otype.s("publication_licence")),
        "validated_bibl_scopes": len(F.otype.s("bibl_scope")),
        "validated_dimensions": len(F.otype.s("dimension")),
        "validated_images": len(F.otype.s("image")),
        "validated_nested_surfaces": nested_surfaces,
        "validated_citations": citations,
        "dated_inscriptions_with_typed_derivative": len(dated),
        "settlement_refs": len(referenced_places),
    }


def _validate_language_source_provenance(api: Any) -> dict[str, int]:
    """Pinned authentic Brown evidence: source lang tags survive native TF reload."""
    F, L, T = api.F, api.L, api.T

    abil = T.nodeFromSection(("abil0001",))
    chor = T.nodeFromSection(("chor0001",))
    beth = T.nodeFromSection(("beth0023",))
    caes = T.nodeFromSection(("caes0044",))
    if abil is None or chor is None or beth is None or caes is None:
        raise SystemExit("missing pinned language provenance canary record")

    # Actual p@xml:lang=heb must remain traceable even if authoritative
    # aligned segmented Aramaic word evidence corrects its effective language.
    aramaic = [
        n for n in L.d(chor, otype="sign")
        if F.layer.v(n) == "transcription"
        and F.lang_original.v(n) == "heb"
        and F.lang_origin.v(n) == "p"
        and F.script.v(n) == "Hebr"
    ]
    if len(aramaic) < 10:
        raise SystemExit("chor0001 source paragraph language provenance was lost")
    arc_words = [
        w for w in L.d(chor, otype="word")
        if F.lang.v(w) == "arc"
        and F.lang_original.v(w) == "arc"
        and F.lang_origin.v(w) == "w"
    ]
    if not arc_words:
        raise SystemExit("chor0001 aligned Aramaic word source provenance was lost")
    if not any(set(L.d(w, otype="sign")).intersection(aramaic) for w in arc_words):
        raise SystemExit("chor0001 segmented words no longer align with native signs")

    # Stronger than an isolated canary: every source paragraph Hebrew-letter
    # sign covered by drift-free selected 'arc' tokens must now answer 'arc'.
    source_signs = set(aramaic)
    corrected: set[int] = set()
    for word in arc_words:
        if F.segmentation_status.v(word) != "projected":
            continue
        for sign in L.d(word, otype="sign"):
            if sign not in source_signs:
                continue
            if (
                F.lang.v(sign) != "arc"
                or F.lang_source.v(sign) != "transcription_segmented"
            ):
                raise SystemExit(
                    f"chor0001 selected Aramaic word still has mislabeled sign {sign}"
                )
            corrected.add(sign)
    if len(corrected) < 10:
        raise SystemExit("chor0001 source-backed sign language coverage is too low")

    # Genuine div/@xml:lang=heb over source-backed Aramaic words is
    # independently present in authenticated Brown abil0001.
    div_aramaic = [
        n for n in L.d(abil, otype="sign")
        if F.layer.v(n) == "transcription"
        and F.lang_original.v(n) == "heb"
        and F.lang_origin.v(n) == "div"
        and F.script.v(n) == "Hebr"
        and F.lang.v(n) == "arc"
        and F.lang_source.v(n) == "transcription_segmented"
    ]
    if len(div_aramaic) < 5:
        raise SystemExit("abil0001 selected division-scope Aramaic signs not corrected")

    # Explicit Aramaic written in Greek letters is a distinct kind of source
    # declaration: a future container override must not erase it.
    greek_aramaic = [
        n for n in L.d(beth, otype="sign")
        if F.glyph.v(n) == "β"
        and F.lang.v(n) == "arc-Grek"
        and F.lang_original.v(n) == "arc-Grek"
        and F.lang_origin.v(n) == "foreign"
        and F.script.v(n) == "Grek"
    ]
    if not greek_aramaic:
        raise SystemExit("beth0023 explicit foreign Aramaic language lost")

    # Actual trailing source whitespace must survive both the parser and TF's
    # string feature file serialization (not merely the in-memory IR).
    egyptian_names = [
        n for n in L.d(caes, otype="entity")
        if F.entity_kind.v(n) == "person"
        and F.lang_original.v(n) == "egy "
        and F.lang_origin.v(n) == "persName"
    ]
    if not egyptian_names:
        raise SystemExit("caes0044 source xml:lang trailing whitespace was lost")

    return {
        "chor0001_aramaic_signs_with_source_p": len(aramaic),
        "chor0001_corrected_selected_arc_signs": len(corrected),
        "chor0001_segmented_arc_words": len(arc_words),
        "abil0001_corrected_div_arc_signs": len(div_aramaic),
        "beth0023_explicit_foreign_greek_signs": len(greek_aramaic),
        "caes0044_egyptian_name_origin_sources": len(egyptian_names),
    }


_NAME_LANG_CODES = {
    "x-Nabatean": "arc",
    "x-Palmyran": "arc",
    "x-Arabic": "ara",
    "x-Semitic": "other",
    "x-greek-hebrew": "other",
    "x-unknown": "unknown",
    "he": "heb",
    "heb": "heb",
    "la": "lat",
    "hbo": "hbo",
    "grc": "grc",
    "arc": "arc",
    "egy": "egy",
    "xcl": "xcl",
}


def _validate_name_origins_from_ir(ir: Any, counts: Counter[str]) -> None:
    """Validate every explicit translation persName origin independently."""
    for entity in ir.nodes_of_type(NodeType.ENTITY):
        if (
            entity.feature("entity_kind") != "person"
            or entity.feature("layer") != "translation"
        ):
            continue
        raw = entity.feature("name_lang_original")
        if raw is None:
            if entity.feature("lang_origin") == "persName":
                raise SystemExit("missing name_lang_original on explicit translation name")
            continue
        if not isinstance(raw, str) or raw.strip() not in _NAME_LANG_CODES:
            raise SystemExit("unmapped explicit translation name-language source code")
        if (
            entity.feature("name_lang") != _NAME_LANG_CODES[raw.strip()]
            or entity.feature("lang") is not None
            or entity.feature("lang_source") is not None
            or entity.feature("lang_original") != raw
            or entity.feature("lang_origin") != "persName"
        ):
            raise SystemExit("translation name origin overlaps effective text language")
        counts[raw.strip()] += 1


def _validate_native_name_origins(api: Any) -> dict[str, int]:
    """Check three authentic pinned Brown translation names after TF reload."""
    canaries = (
        ("caes0044", "egy ", "egy"),
        ("hamm0054", "x-Arabic ", "ara"),
        ("beth0117", "x-Nabatean ", "arc"),
    )
    verified: dict[str, int] = {}
    for record, raw, mapped in canaries:
        owner = api.T.nodeFromSection((record,))
        if owner is None:
            raise SystemExit(f"missing name-origin canary {record}")
        entities = [
            node for node in api.L.d(owner, otype="entity")
            if api.F.entity_kind.v(node) == "person"
            and api.F.name_lang_original.v(node) == raw
            and api.F.name_lang.v(node) == mapped
            and api.F.lang.v(node) is None
            and api.F.lang_original.v(node) == raw
            and api.F.lang_origin.v(node) == "persName"
        ]
        if not entities:
            raise SystemExit(f"{record}: translation name origin lost")
        verified[record] = len(entities)
        if record == "caes0044":
            letters = [
                slot
                for node in entities for slot in api.L.d(node, otype="sign")
                if (glyph := api.F.glyph.v(slot)) and glyph.isalpha()
            ]
            if not letters or any(api.F.lang.v(slot) != "eng" for slot in letters):
                raise SystemExit("caes0044: English translated name mislabeled Egyptian")
    return verified


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--converter-commit", required=True)
    args = parser.parse_args()

    # Authenticate bytes against the upstream Git subtree, not a caller-supplied
    # provenance string or the agreement of two builds from identical inputs.
    verified_source_tree = require_source_tree_sha(
        args.source_dir, expected_sha=PINNED_EPIDOC_SOURCE_TREE
    )
    selected, excluded = inventory_source_files(args.source_dir, source_revision=args.revision)
    if len(selected) != EXPECTED_PARSED or excluded != {
        "aaTestFile.xml": "pinned source test fixture"
    }:
        raise SystemExit("pinned source file accounting changed")
    reports_dir = args.output_dir.with_name(args.output_dir.name + "-reports")
    # Refuse rather than erase any previous research output.
    require_empty_output_directory(reports_dir)

    # Every successful parse is only IR, not a successfully converted TF record.
    # Keep a durable failure ledger separate from the native corpus output.
    parsed_files: list[str] = []
    stage = "parse"
    failing_file: str | None = None
    try:
        register_path = args.source_dir.parent / "data-keep" / "persons.xml"
        if len(selected) >= 1000 and not register_path.is_file():
            raise SystemExit("pinned Brown persons.xml source register is missing")
        register = (
            read_person_register(
                register_path,
                expected_git_sha1=PINNED_PERSONS_BLOB if len(selected) >= 1000 else None,
            )
            if register_path.is_file() else None
        )
        if len(selected) >= 1000 and register is not None and len(register) != 844:
            raise SystemExit("authenticated IIP person register changed")
        person_resolved_entities = 0
        person_distinct_people = 0
        person_unresolved: Counter[str] = Counter()
        irs = []
        node_counts: Counter[str] = Counter()
        edge_counts: Counter[str] = Counter()
        slot_languages: Counter[str] = Counter()
        corrected_heb_script_signs = 0
        name_origin_counts: Counter[str] = Counter()
        corrected_by_origin: Counter[str] = Counter()
        slot_kinds: Counter[str] = Counter()
        sign_count = 0
        point_count = 0
        empty_structural = 0
        token_identities = 0

        for path in selected:
            failing_file = path.name
            ir = parse_epidoc_file(path, source_revision=args.revision)
            if register is not None:
                ir, person_audit = attach_person_register(ir, register)
                person_resolved_entities += int(person_audit["resolved_entities"])
                person_distinct_people += int(person_audit["distinct_people"])
                person_unresolved.update(person_audit["unresolved_targets"])
            irs.append(ir)
            parsed_files.append(path.name)
            if len(selected) >= 1000:
                _validate_name_origins_from_ir(ir, name_origin_counts)
            sign_count += len(ir.signs)
            for sign in ir.signs:
                slot_languages[sign.lang or "und"] += 1
                if (
                    sign.layer.value == "transcription"
                    and sign.lang == "arc"
                    and sign.lang_source == "transcription_segmented"
                    and sign.lang_origin in {"p", "div"}
                    and sign.lang_original is not None
                    and sign.lang_original.strip() == "heb"
                ):
                    corrected_heb_script_signs += 1
                    corrected_by_origin[sign.lang_origin or "<unknown>"] += 1
                slot_kinds[sign.synthetic_kind or "visible"] += 1
            for node in ir.nodes:
                node_counts[node.node_type.value] += 1
                if node.point_index is not None:
                    point_count += 1
                elif not node.sign_keys and node.node_type in {
                    NodeType.EDITION,
                    NodeType.PARAGRAPH,
                }:
                    empty_structural += 1
                if node.node_type == NodeType.WORD:
                    token_identities += 1
                elif (
                    node.node_type == NodeType.MARKUP
                    and node.feature("annotation_source") == "transcription_segmented"
                    and node.feature("token_id") is not None
                    and not node.sign_keys
                ):
                    token_identities += 1
            for edge in ir.edges:
                edge_counts[edge.edge_type.value] += 1

        stage = "ir_validation"
        failing_file = None
        parsed = len(irs)
        edge_count = sum(edge_counts.values())
        node_count = sum(node_counts.values())

        expected = {
            "parsed": EXPECTED_PARSED,
            "signs": EXPECTED_SIGNS,
            "nodes": EXPECTED_NODES + node_counts["person"],
            "edges": EXPECTED_EDGES + edge_counts["person_ref"],
            "points": EXPECTED_POINTS,
            "empty_structural": EXPECTED_EMPTY_STRUCTURAL,
            "segmented_token_identities": EXPECTED_SEGMENTED_TOKEN_IDENTITIES,
        }
        actual = {
            "parsed": parsed,
            "signs": sign_count,
            "nodes": node_count,
            "edges": edge_count,
            "points": point_count,
            "empty_structural": empty_structural,
            "segmented_token_identities": token_identities,
        }
        if actual != expected:
            raise SystemExit(
                "pinned canonical IR accounting changed: "
                + json.dumps({"expected": expected, "actual": actual}, sort_keys=True)
            )

        # Corpus-wide coverage is a pinned-source gate, not a requirement of
        # synthetic one-record failure-accounting tests.
        if parsed == EXPECTED_PARSED and parsed >= 1000 and corrected_heb_script_signs < 1000:
            raise SystemExit(
                "pinned Aramaic source-backed sign correction coverage unexpectedly low: "
                f"{corrected_heb_script_signs}"
            )

        # Independent, source-provenance-aware *post-resolution* audit.
        # Only the full authenticated pinned source is eligible: synthetic
        # failure-ledger tests intentionally substitute one-record fake IR.
        aramaic_language_audit: dict[str, Any] | None = None
        if parsed == EXPECTED_PARSED and parsed >= 1000:
            coverage = AramaicLanguageAudit()
            for ir in irs:
                coverage.ingest(ir)
            aramaic_language_audit = coverage.report()
            if aramaic_language_audit["corrected_signs"] != corrected_heb_script_signs:
                raise SystemExit("independent Aramaic correction audit count disagrees")
            if aramaic_language_audit["corrected_by_source_origin"] != dict(
                sorted(corrected_by_origin.items())
            ):
                raise SystemExit("pinned Aramaic source-origin correction counts disagree")
            if corrected_by_origin["p"] != 5159:
                raise SystemExit("pinned paragraph-scope Aramaic corrections changed")
            if corrected_heb_script_signs + aramaic_language_audit["remaining_signs"] != 45162:
                raise SystemExit("pinned Aramaic script-like population did not reconcile")
            if corrected_by_origin["div"] < 1000:
                raise SystemExit("pinned division-scope Aramaic evidence coverage too low")
            if not aramaic_language_audit["remaining_signs"]:
                raise SystemExit("pinned source unexpectedly has no residual heb signs")
            unaligned = aramaic_language_audit["no_selected_word_evidence"]
            if (
                unaligned["signs"] != 1786
                or sum(unaligned["reasons"].values()) != 1786
                or aramaic_language_audit["reasons"].get("no_selected_word") != 1786
            ):
                raise SystemExit("authenticated unaligned Aramaic signs failed reconciliation")
            editorial = aramaic_language_audit["selected_uncovered_editorial_evidence"]
            if (
                editorial["signs"] != 179
                or sum(editorial["reading_roles"].values()) != 179
                or sum(editorial["markup_branches"].values()) != 179
                or not 0 <= editorial["alternate_branch_has_projected_word"] <= 179
            ):
                raise SystemExit("authenticated uncovered editorial partition disagrees")
            by_textpart = aramaic_language_audit["selected_uncovered_textpart_evidence"]
            if (
                by_textpart["signs"] != 168
                or sum(by_textpart["scopes"].values()) != 168
                or editorial["markup_branches"].get("none") != 168
                or editorial["markup_branches"].get("reg") != 11
                or len(by_textpart["normalized_no_editorial_examples"]) != 1
            ):
                raise SystemExit("pinned non-editorial textpart evidence mismatch")
            mare = next(
                (ir for ir in irs if ir.identity.inscription_id == "mare0134"),
                None,
            )
            if (
                mare is None
                or not any(
                    part.feature("section_part") == "transcription:column:b"
                    for part in mare.nodes_of_type(NodeType.TEXTPART)
                )
                or not any(
                    part.feature("section_part") == "transcription:left-margin-lines"
                    for part in mare.nodes_of_type(NodeType.TEXTPART)
                )
            ):
                raise SystemExit("pinned mare0134 multi-textpart source canary changed")
            bshe = next(
                (ir for ir in irs if ir.identity.inscription_id == "bshe0157"),
                None,
            )
            if bshe is None:
                raise SystemExit("missing original Brown editorial canary bshe0157")
            bshe_words = {
                key for word in bshe.nodes_of_type(NodeType.WORD)
                for key in word.sign_keys
            }
            bshe_reg_keys = {
                key for node in bshe.nodes_of_type(NodeType.MARKUP)
                if node.feature("kind") == "reg" for key in node.sign_keys
            }
            if not any(
                sign.key in bshe_reg_keys
                and sign.key not in bshe_words
                and sign.lang == "heb"
                and sign.reading_role == "normalized"
                and sign.lang_original == "heb"
                for sign in bshe.signs
                if sign.layer.value == "transcription" and sign.glyph
            ):
                raise SystemExit("bshe0157 source-only orig/normalized reg canary lost")
            drift = aramaic_language_audit["drift_source_evidence"]
            if (
                aramaic_language_audit["reasons"].get(
                    "drift_or_uncertain_word_overlap"
                ) != 2
                or len(drift) != 2
                or {row["record"] for row in drift} != {"idum0375"}
                or {row["sign_key"] for row in drift}
                != {"idum0375#s19", "idum0375#s20"}
                or any(
                    not any(
                        w["source_id"] == "idum0375-8"
                        and w["status"] == "projected_with_source_drift"
                        for w in row["words"]
                    )
                    for row in drift
                )
            ):
                raise SystemExit("authenticated source-drift ambiguity inventory changed")
            anun = next(
                (ir for ir in irs if ir.identity.inscription_id == "anun0005"),
                None,
            )
            if (
                anun is None
                or anun.identity.main_lang != "arc"
                or anun.nodes_of_type(NodeType.SEGMENTATION)
                or not any(
                    sign.glyph and sign.lang == "heb"
                    and sign.lang_origin == "div"
                    for sign in anun.signs
                    if sign.layer.value == "transcription"
                )
            ):
                raise SystemExit("anun0005 missing authentic absent-segmentation canary")

        if parsed == EXPECTED_PARSED and parsed >= 1000 and not name_origin_counts:
            raise SystemExit("pinned source has no explicit translation personal-name origins")

        stage = "tf_write"
        require_empty_output_directory(args.output_dir)
        write_tf_corpus(
            tuple(irs),
            args.output_dir,
            converter_commit=args.converter_commit,
        )

        stage = "tf_reload"
        api: Any = Fabric(locations=str(args.output_dir), silent=True).loadAll(silent=True)
        if not api:
            raise SystemExit("Text-Fabric failed to load generated pinned corpus")

        stage = "native_integrity"
        loaded_node_counts = {
            node_type: len(api.F.otype.s(node_type))
            for node_type in ("sign", *sorted(node_counts))
        }
        if loaded_node_counts["sign"] != sign_count:
            raise SystemExit(
                f"loaded sign count {loaded_node_counts['sign']} != {sign_count}"
            )
        for node_type, count in node_counts.items():
            if loaded_node_counts[node_type] != count:
                raise SystemExit(
                    f"loaded {node_type} count {loaded_node_counts[node_type]} != {count}"
                )

        validated_oslots_nodes = validate_oslots_mapping(
            api.E.oslots.items(),
            sign_count=sign_count,
            node_count=node_count,
        )

        loaded_edge_counts: dict[str, int] = {}
        for edge_type, expected_count in edge_counts.items():
            feature = api.Es(edge_type)
            count = sum(len(targets) for _, targets in feature.items())
            loaded_edge_counts[edge_type] = count
            if count != expected_count:
                raise SystemExit(
                    f"loaded edge {edge_type} count {count} != {expected_count}"
                )

        point_nodes = tuple(node for node, _ in api.Fs("point_index").items())
        if len(point_nodes) != EXPECTED_POINTS:
            raise SystemExit(f"loaded point count {len(point_nodes)} != {EXPECTED_POINTS}")
        for node in point_nodes:
            slots = tuple(api.L.d(node, otype="sign"))
            if len(slots) != 1:
                raise SystemExit(f"point node {node} has {len(slots)} technical slots")
            relation = api.Fs("point_relation").v(node)
            if relation not in {"before", "after"}:
                raise SystemExit(f"point node {node} has invalid relation {relation!r}")

        empty_values = tuple(api.Fs("empty").items())
        if not empty_values:
            raise SystemExit("generated corpus lacks empty structural markers")

        shutil.rmtree(args.output_dir / ".tf", ignore_errors=True)
        for path in args.output_dir.glob("*.tf"):
            if "@dateWritten=" in path.read_text(encoding="utf-8"):
                raise SystemExit(f"volatile dateWritten remains in {path.name}")

        metadata_queries = _validate_native_metadata_queries(api)
        language_sources = _validate_language_source_provenance(api)
        name_origin_canaries = _validate_native_name_origins(api)
        person_canaries: dict[str, str] = {}
        if register is not None and len(selected) >= 1000:
            if (
                person_resolved_entities < 500
                or person_distinct_people < 500
                or person_resolved_entities != edge_counts["person_ref"]
                or person_distinct_people != node_counts["person"]
            ):
                raise SystemExit("pinned native IIP personal-name resolution coverage changed")
            for record_id, person_id, expected_sex, expected_faith in (
                ("beth0001", "beth0001p01", "1", "Jewish"),
                ("beth0042", "beth0042p01", "1", "Jewish"),
            ):
                root = api.T.nodeFromSection((record_id,))
                if root is None:
                    raise SystemExit(f"pinned person canary absent: {record_id}")
                persons = [
                    node for node in api.L.d(root, otype="person")
                    if api.F.person_id.v(node) == person_id
                ]
                if len(persons) != 1:
                    raise SystemExit(f"{record_id}: canonical person resolution failed")
                person = persons[0]
                if (
                    api.F.sex.v(person) != expected_sex
                    or api.F.faith.v(person) != expected_faith
                ):
                    raise SystemExit(f"{record_id}: real person sex/faith lost")
                linked = [
                    entity for entity in api.L.d(root, otype="entity")
                    if person in api.E.person_ref.f(entity)
                    and api.F.ref.v(entity) == f"persons.xml#{person_id}"
                ]
                if not linked:
                    raise SystemExit(f"{record_id}: person edge or original ref lost")
                person_canaries[record_id] = person_id
        report = {
            **actual,
            "metadata_queries": metadata_queries,
            "language_source_canaries": language_sources,
            "name_origin_codes": dict(sorted(name_origin_counts.items())),
            "name_origin_canaries": name_origin_canaries,
            "person_register": {
                "source_git_blob": PINNED_PERSONS_BLOB if register is not None else None,
                "entries": len(register) if register is not None else 0,
                "resolved_entities": person_resolved_entities,
                "distinct_people": person_distinct_people,
                "unresolved_targets": dict(sorted(person_unresolved.items())),
                "canaries": person_canaries,
            },
            "corrected_heb_script_transcription_signs": corrected_heb_script_signs,
            "corrected_heb_script_signs_by_origin": dict(sorted(corrected_by_origin.items())),
            "aramaic_transcription_language_audit": aramaic_language_audit,
            "node_counts": dict(sorted(node_counts.items())),
            "edge_counts": dict(sorted(edge_counts.items())),
            "tf_files": len(tuple(args.output_dir.glob("*.tf"))),
            "validated_oslots_nodes": validated_oslots_nodes,
        }
        stage = "reproducibility"
        # Rebuild from source in a separate fresh directory, not the cached
        # in-memory canonical IR. Compare every native TF feature bytewise.
        # Drop first-build memory before the independent parse of 5,535 files.
        irs.clear()
        del api
        gc.collect()
        with tempfile.TemporaryDirectory(
            prefix="pinned-tf-independent-",
            dir=args.output_dir.parent,
        ) as fresh_directory:
            second_dir = Path(fresh_directory)
            write_tf_corpus(
                (
                    attach_person_register(
                        parse_epidoc_file(path, source_revision=args.revision),
                        register,
                    )[0]
                    if register is not None
                    else parse_epidoc_file(path, source_revision=args.revision)
                    for path in selected
                ),
                second_dir,
                converter_commit=args.converter_commit,
            )
            feature_hashes = compare_tf_feature_hashes(args.output_dir, second_dir)
        if len(feature_hashes) != report["tf_files"]:
            raise SystemExit("not all native TF features were hashed")

        complete = {
            **report,
            "status": "success",
            "source_revision": args.revision,
            "verified_source_tree_git_sha1": verified_source_tree,
            "converter_commit": args.converter_commit,
            "source_files": {
                "converted": [path.name for path in selected],
                "excluded": excluded,
                "failed": [],
            },
            "slot_languages": dict(sorted(slot_languages.items())),
            "slot_kinds": dict(sorted(slot_kinds.items())),
            "tf_feature_hashes": feature_hashes,
            "reproducible_builds": 2,
        }
        stage = "report_write"
        write_build_reports(reports_dir, complete)
        print(json.dumps(complete, sort_keys=True))
        return 0
    except (Exception, SystemExit) as error:
        selected_names = [path.name for path in selected]
        remainder = (
            selected_names[len(parsed_files) + (1 if failing_file else 0):]
            if stage == "parse"
            else []
        )
        failed: dict[str, object] = {
            "filename": failing_file,
            "stage": stage,
            "error_type": type(error).__name__,
        }
        # No raw XML or exception messages: source exception text may embed data.
        # We only count a source as converted on the all-green success path.
        failure_report: dict[str, object] = {
            "status": "failed",
            "source_revision": args.revision,
            "verified_source_tree_git_sha1": verified_source_tree,
            "converter_commit": args.converter_commit,
            "failed_stage": stage,
            "source_files": {
                "converted": [],
                "parsed": parsed_files,
                "excluded": excluded,
                "failed": [failed],
                "unprocessed": remainder,
            },
        }
        try:
            write_build_reports(reports_dir, failure_report)
        except OSError as report_error:
            error.add_note(
                "Could not persist pinned conversion failure report: "
                + type(report_error).__name__
            )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
