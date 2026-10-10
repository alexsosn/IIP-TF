"""Inventory language-code values per TF feature and node type for issue #52."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from iip_tf.ir import NodeType
from iip_tf.text_parser import parse_epidoc_file

_LANGUAGE_FEATURES = ("lang", "main_lang", "other_langs", "candidate_langs")
_EXAMPLES_PER_VALUE = 8


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    parsed = 0
    values: dict[str, Counter[str]] = defaultdict(Counter)
    tokens: dict[str, Counter[str]] = defaultdict(Counter)
    records: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    lang_source: Counter[str] = Counter()

    for path in sorted(args.source_dir.glob("*.xml")):
        if "test" in path.name.lower():
            continue
        ir = parse_epidoc_file(path, source_revision=args.revision)
        parsed += 1
        record = ir.identity.inscription_id

        for sign in ir.signs:
            key = "sign:lang"
            value = sign.lang if sign.lang is not None else "<none>"
            values[key][value] += 1
            records[key][value].add(record)
            lang_source[f"sign:{sign.lang_source}"] += 1

        for node in ir.nodes:
            features = dict(node.features)
            for name in _LANGUAGE_FEATURES:
                raw = features.get(name)
                if raw is None:
                    continue
                key = f"{node.node_type.value}:{name}"
                value = str(raw)
                values[key][value] += 1
                records[key][value].add(record)
                for token in value.split():
                    tokens[key][token] += 1
            if "lang_source" in features and node.node_type is not NodeType.INSCRIPTION:
                lang_source[f"{node.node_type.value}:{features['lang_source']}"] += 1

    all_tokens: Counter[str] = Counter()
    for counter in tokens.values():
        all_tokens.update(counter)
    for key, counter in values.items():
        if key.startswith("sign:"):
            all_tokens.update({v: c for v, c in counter.items() if v != "<none>"})

    report = {
        "revision": args.revision,
        "parsed": parsed,
        "values": {
            key: [
                {
                    "value": value,
                    "count": count,
                    "records": len(records[key][value]),
                    "examples": sorted(records[key][value])[:_EXAMPLES_PER_VALUE],
                }
                for value, count in counter.most_common()
            ]
            for key, counter in sorted(values.items())
        },
        "multi_token_features": {
            key: dict(counter.most_common())
            for key, counter in sorted(tokens.items())
            if any(" " in value for value in values[key])
        },
        "distinct_codes": dict(all_tokens.most_common()),
        "lang_source": dict(sorted(lang_source.items())),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
