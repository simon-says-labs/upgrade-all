"""A report with made-up data, for the README pictures and for trying out the design.

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from . import report
from .run import HookResult, RunResult, StepRow

SAMPLE_LOG = """―― upgrade-all: brew upgrade topgrade ――
==> Upgrading topgrade 17.12.2 -> 17.12.3
―― 08:55:31 - Brew (ARM) ――
==> Upgrading 4 outdated packages
―― 09:12:02 - Summary ――
Brew (ARM): OK
Brew Cask (ARM): OK
npm: FAILED
Visual Studio Code extensions: OK
pipx: OK
Microsoft Office: SKIPPED
"""

SAMPLE_RETRY = """―― 09:12:40 - npm ――
added 12 packages
―― 09:12:52 - Summary ――
npm: OK
"""


def write_sample(target: Path, language: str = "en") -> None:
    folder = Path(tempfile.mkdtemp(prefix="upgrade-all-sample-"))
    (folder / "2026-10-06_08-55-26.log").write_text(SAMPLE_LOG)
    (folder / "2026-10-06_08-55-26_retry.log").write_text(SAMPLE_RETRY)
    hook_log = folder / "2026-10-06_08-55-26_hook_50-media-tools.log"
    hook_log.write_text("ComfyUI: 17 new commits\nSummary: 3 updated, 9 current\n")
    result = RunResult(
        started="2026-10-06T08:55:26", finished="2026-10-06T09:13:04", seconds=1058, host="studio-mac",
        language=language, topgrade_path="/opt/homebrew/Cellar/topgrade/17.12.3/bin/topgrade",
        version_before="17.12.2", version_after="17.12.3", pre_exit=0, main_exit=1,
        rows=[StepRow("Brew (ARM)", "OK", "ok"), StepRow("Brew Cask (ARM)", "OK", "ok"),
              StepRow("npm", "FAILED", "failed", "OK", "ok", True),
              StepRow("Visual Studio Code extensions", "OK", "ok"), StepRow("pipx", "OK", "ok"),
              StepRow("Microsoft Office", "SKIPPED", "skipped")],
        retried=["npm"], fixed=["npm"], services_restarted=["ollama"],
        hooks=[HookResult("50-media-tools", 0, "ok", "3 updated, 9 current", str(hook_log))],
        log_file=str(folder / "2026-10-06_08-55-26.log"),
        log_display="~/Library/Logs/upgrade-all/2026-10-06_08-55-26.log", retry_log_file=str(folder / "2026-10-06_08-55-26_retry.log"),
        interval_days=3, outcome="fixed", exit_code=0)
    target.write_text(report.render(result), encoding="utf-8")
