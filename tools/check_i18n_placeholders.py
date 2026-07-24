#!/usr/bin/env python3
"""Validate placeholder, ICU, format, and HTML-tag parity in zh-CN resources."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import TypeAlias


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import patch_windowsapps_json_only  # noqa: E402


RESOURCE_PAIRS = {
    "desktop": {
        "local": ROOT / "resources" / "desktop-zh-CN.json",
        "installed_en": Path("resources/en-US.json"),
    },
    "frontend": {
        "local": ROOT / "resources" / "frontend-zh-CN.json",
        "installed_en": Path("resources/ion-dist/i18n/en-US.json"),
    },
    "statsig": {
        "local": ROOT / "resources" / "statsig-zh-CN.json",
        "installed_en": Path("resources/ion-dist/i18n/statsig/en-US.json"),
    },
}

IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9]*)\b([^>]*)>")
ICU_KINDS = {"plural", "select", "selectordinal"}

CounterValue: TypeAlias = str | tuple[str, ...]
Signature: TypeAlias = dict[str, Counter[CounterValue]]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def matching_brace(value: str, start: int) -> int:
    depth = 0
    for index in range(start, len(value)):
        if value[index] == "{":
            depth += 1
        elif value[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def split_top_level(value: str, max_splits: int = 2) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(value):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "," and depth == 0 and len(parts) < max_splits:
            parts.append(value[start:index])
            start = index + 1
    parts.append(value[start:])
    return parts


def empty_signature() -> Signature:
    return {
        "variables": Counter(),
        "icu": Counter(),
        "formats": Counter(),
        "tags": Counter(),
        "errors": Counter(),
    }


def parse_icu_options(value: str, signature: Signature) -> tuple[str, ...] | None:
    labels: list[str] = []
    index = 0
    while index < len(value):
        while index < len(value) and value[index].isspace():
            index += 1
        if index >= len(value):
            break

        label_start = index
        while index < len(value) and not value[index].isspace() and value[index] != "{":
            index += 1
        label = value[label_start:index]
        while index < len(value) and value[index].isspace():
            index += 1
        if not label or index >= len(value) or value[index] != "{":
            return None

        end = matching_brace(value, index)
        if end < 0:
            return None
        labels.append(label)
        parse_message(value[index + 1 : end], signature)
        index = end + 1
    return tuple(sorted(labels))


def parse_block(value: str, signature: Signature) -> None:
    parts = split_top_level(value)
    variable = parts[0].strip()
    if not IDENTIFIER_RE.fullmatch(variable):
        signature["errors"][f"invalid-placeholder:{value}"] += 1
        return

    signature["variables"][variable] += 1
    if len(parts) == 1:
        return

    kind = parts[1].strip().lower()
    detail = parts[2].strip() if len(parts) == 3 else ""
    if kind in ICU_KINDS:
        labels = parse_icu_options(detail, signature)
        if labels is None:
            signature["errors"][f"invalid-icu:{value}"] += 1
            return
        signature["icu"][(variable, kind, *labels)] += 1
        return

    signature["formats"][(variable, kind, detail)] += 1


def parse_message(value: str, signature: Signature) -> None:
    index = 0
    while index < len(value):
        if value[index] == "}":
            signature["errors"]["unexpected-closing-brace"] += 1
            index += 1
            continue
        if value[index] != "{":
            index += 1
            continue

        end = matching_brace(value, index)
        if end < 0:
            signature["errors"]["unclosed-placeholder"] += 1
            return
        parse_block(value[index + 1 : end], signature)
        index = end + 1


def message_signature(value: str) -> Signature:
    signature = empty_signature()
    parse_message(value, signature)
    for match in TAG_RE.finditer(value):
        closing, name, suffix = match.groups()
        if closing:
            tag_kind = "close"
        elif suffix.rstrip().endswith("/"):
            tag_kind = "self"
        else:
            tag_kind = "open"
        signature["tags"][(tag_kind, name)] += 1
    return signature


def counter_delta(source: Counter[CounterValue], target: Counter[CounterValue]) -> str:
    missing = source - target
    extra = target - source
    parts = []
    if missing:
        parts.append(f"missing={dict(missing)}")
    if extra:
        parts.append(f"extra={dict(extra)}")
    return " ".join(parts)


def signature_differences(source: Signature, target: Signature) -> list[str]:
    differences = []
    for field in ("variables", "icu", "formats", "tags", "errors"):
        if source[field] != target[field]:
            differences.append(f"{field}: {counter_delta(source[field], target[field])}")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that zh-CN resources preserve source placeholders and ICU structure"
    )
    parser.add_argument("--app-dir", type=Path, default=None)
    parser.add_argument("--max-errors", type=int, default=50)
    args = parser.parse_args()

    app_dir = args.app_dir or patch_windowsapps_json_only.find_claude_package()
    if not app_dir:
        raise SystemExit("Claude app directory not found; pass --app-dir")

    mismatch_count = 0
    checked_count = 0
    for name, spec in RESOURCE_PAIRS.items():
        source_path = app_dir / spec["installed_en"]
        target_path = spec["local"]
        if not source_path.exists():
            print(f"SKIP {name}: source resource missing at {source_path}")
            continue
        if not target_path.exists():
            raise SystemExit(f"Missing local resource: {target_path}")

        source_data = load_json(source_path)
        target_data = load_json(target_path)
        resource_mismatches = 0
        for key, source_value in source_data.items():
            target_value = target_data.get(key)
            if not isinstance(source_value, str) or not isinstance(target_value, str):
                continue
            checked_count += 1
            differences = signature_differences(
                message_signature(source_value),
                message_signature(target_value),
            )
            if not differences:
                continue

            mismatch_count += 1
            resource_mismatches += 1
            if mismatch_count <= args.max_errors:
                print(f"MISMATCH {name}:{key}")
                for difference in differences:
                    print(f"  {difference}")
                print(f"  EN: {source_value}")
                print(f"  ZH: {target_value}")

        print(
            f"{name}: checked={len(source_data)} "
            f"missing_keys={len(set(source_data) - set(target_data))} "
            f"placeholder_mismatches={resource_mismatches}"
        )

    print(f"Checked string pairs: {checked_count}")
    print(f"Total placeholder mismatches: {mismatch_count}")
    return 1 if mismatch_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
