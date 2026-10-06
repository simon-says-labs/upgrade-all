#!/usr/bin/env python3
"""Builds upgrade_all/data/steps.json from topgrade's source.

Topgrade prints a summary with a label per step ("Brew (ARM): FAILED"), but `--only` wants the
step's id ("brew_formula"). Both come from src/step.rs: each enum variant (snake_case = id) runs
`runner.execute(*self, "<label>", ...)`. Translated words of the summary (Summary, FAILED, ...)
come from locales/app.yml.

    python3 tools/update_steps.py v17.12.3

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/topgrade-rs/topgrade/%s/%s"
TARGET = Path(__file__).resolve().parents[1] / "upgrade_all" / "data" / "steps.json"
WORDS = ("Summary", "OK", "FAILED", "SKIPPED", "IGNORED")


def snake_case(name: str) -> str:
    """Like heck's snake_case, which clap uses for the enum: AppMan -> app_man, AM -> am."""
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+\d*|[A-Z]+\d*|\d+", name)
    return "_".join(w.lower() for w in words)


def labels_from_step_rs(source: str) -> dict:
    """{label: id} for every runner.execute(*self, "label", ...) inside a match arm."""
    arms = list(re.finditer(r"\n {12}(\w+) =>", source))
    result = {}
    for i, arm in enumerate(arms):
        end = arms[i + 1].start() if i + 1 < len(arms) else len(source)
        for label in re.findall(r'runner\.execute\(\s*\*self,\s*(?:t!\()?\s*"([^"]+)"', source[arm.start():end]):
            result.setdefault(label, snake_case(arm.group(1)))
    return result


def words_from_app_yml(source: str) -> dict:
    """{"Summary": ["Summary", "Zusammenfassung", ...], "FAILED": [...], ...} without a YAML library."""
    result, current = {}, None
    for line in source.splitlines():
        top = re.match(r'^"(.+)":\s*$', line)
        if top:
            current = top.group(1) if top.group(1) in WORDS else None
            continue
        value = re.match(r'^\s+[A-Za-z_]+:\s*"(.*)"\s*$', line)
        if current and value:
            result.setdefault(current, [])
            if value.group(1) not in result[current]:
                result[current].append(value.group(1))
    return result


def fetch(version: str, path: str) -> str:
    with urllib.request.urlopen(RAW % (version, path), timeout=60) as response:
        return response.read().decode()


def main(version: str) -> int:
    data = {"topgrade": version.lstrip("v"),
            "labels": dict(sorted(labels_from_step_rs(fetch(version, "src/step.rs")).items())),
            "words": words_from_app_yml(fetch(version, "locales/app.yml"))}
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print("%d labels, words: %s" % (len(data["labels"]), ", ".join(sorted(data["words"]))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "v17.12.3"))
