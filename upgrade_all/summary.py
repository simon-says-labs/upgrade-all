"""Reads topgrade's summary block, whatever language topgrade printed it in.

    ―― 16:40:01 - Zusammenfassung ――
    Brew (ARM): OK
    npm: FEHLGESCHLAGEN

Labels and the translated words come from topgrade's own source (data/steps.json,
built by tools/update_steps.py).

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent / "data" / "steps.json").read_text())
ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
HEADING = re.compile(r"^―― .*―― *$")
ACCESS_DENIED = re.compile(r"EPERM|Operation not permitted|colima is not running", re.I)


def _word_set(key: str) -> set:
    return {w.upper() for w in DATA["words"].get(key, [key])}


SUMMARY_WORDS = set(DATA["words"]["Summary"])
FAILED = _word_set("FAILED")
OK = _word_set("OK")
SKIPPED = _word_set("SKIPPED") | _word_set("IGNORED")


def clean(text: str) -> str:
    return ANSI.sub("", text)


def summary_lines(log_text: str) -> list:
    """The lines of the LAST summary block, without colour codes and empty lines."""
    lines = clean(log_text).splitlines()
    start = None
    for i, line in enumerate(lines):
        if HEADING.match(line.strip()) and any(word in line for word in SUMMARY_WORDS):
            start = i
    if start is None:
        return []
    result = []
    for line in lines[start + 1:]:
        if HEADING.match(line.strip()):
            break
        if line.strip():
            result.append(line.rstrip())
    return result


def steps(log_text: str) -> list:
    """[(label, status)] from the summary; status is the word topgrade printed."""
    result = []
    for line in summary_lines(log_text):
        match = re.match(r"^(.*?):\s*(\S.*)$", line)
        if match:
            result.append((match.group(1).strip(), match.group(2).strip()))
    return result


def outcome(status: str) -> str:
    """ok | failed | skipped | other for a status word in any language."""
    word = status.strip().upper()
    if word in FAILED:
        return "failed"
    if word in OK:
        return "ok"
    if word in SKIPPED:
        return "skipped"
    return "other"


def step_id(label: str):
    """topgrade's --only id for a summary label, or None for unknown labels."""
    return DATA["labels"].get(label)


def access_denied(log_text: str) -> bool:
    return bool(ACCESS_DENIED.search(clean(log_text)))
