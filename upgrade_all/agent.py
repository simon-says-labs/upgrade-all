"""Installing, removing and inspecting the LaunchAgent, and asking macOS for access again.

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from . import __version__
from .config import AGENT_LABEL, Config, Paths

PYTHON = "/usr/bin/python3"


def plist_path(home: Path) -> Path:
    return home / "Library" / "LaunchAgents" / (AGENT_LABEL + ".plist")


def agent_plist(paths: Paths, config: Config, python: str = PYTHON) -> dict:
    return {
        "Label": AGENT_LABEL,
        "ProgramArguments": [python, "-m", "upgrade_all", "run"],
        "WorkingDirectory": str(paths.app),
        "EnvironmentVariables": {"PYTHONPATH": str(paths.app), "PYTHONDONTWRITEBYTECODE": "1"},
        "StartInterval": int(float(config.interval_days) * 86400),
        "RunAtLoad": False,
        "ProcessType": "Background",
        "StandardOutPath": str(paths.logs / "launchd.out.log"),
        "StandardErrorPath": str(paths.logs / "launchd.err.log"),
    }


def launchctl(*args) -> int:
    return subprocess.run(["launchctl"] + list(args), capture_output=True).returncode


def install(paths: Paths, home: Path, source: Path, with_agent: bool = True) -> int:
    """Copies the program, keeps an existing config, writes and loads the LaunchAgent."""
    if sys.platform != "darwin" and with_agent:
        print("The LaunchAgent needs macOS. Use --no-agent to install the files only.")
        return 2
    for folder in (paths.support, paths.logs, paths.reports, paths.hooks):
        folder.mkdir(parents=True, exist_ok=True)
    target = paths.app / "upgrade_all"
    if target.exists():  # an older copy of the program: to the Trash, never deleted
        old = home / ".Trash" / ("upgrade-all-app-%s" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        old.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(old))
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if paths.config.exists():
        config = Config.load(paths.config)
        print("Kept settings: %s" % paths.config)
    else:
        config = Config()
        config.save(paths.config)
        print("Settings: %s" % paths.config)
    launcher = paths.support / "upgrade-all"
    launcher.write_text('#!/bin/sh\nPYTHONPATH="%s" exec %s -m upgrade_all "$@"\n' % (paths.app, PYTHON))
    launcher.chmod(0o755)
    print("Command: %s  (link it into your PATH if you like)" % launcher)
    if with_agent:
        plist = plist_path(home)
        plist.parent.mkdir(parents=True, exist_ok=True)
        with open(plist, "wb") as f:
            plistlib.dump(agent_plist(paths, config), f)
        domain = "gui/%d" % os.getuid()
        launchctl("bootout", "%s/%s" % (domain, AGENT_LABEL))
        if launchctl("bootstrap", domain, str(plist)) != 0:
            print("Could not load %s" % plist)
            return 1
        launchctl("enable", "%s/%s" % (domain, AGENT_LABEL))
        print("LaunchAgent %s: every %g days" % (AGENT_LABEL, float(config.interval_days)))
    print("Upgrade All %s installed. Run it now with: %s run" % (__version__, launcher))
    return 0


def uninstall(paths: Paths, home: Path, logs_too: bool = False) -> int:
    """Unloads the agent and moves the program (and on request the logs) to the Trash."""
    launchctl("bootout", "gui/%d/%s" % (os.getuid(), AGENT_LABEL))
    trash = home / ".Trash" / ("upgrade-all-%s" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    trash.mkdir(parents=True, exist_ok=True)
    moved = []
    for path in [plist_path(home), paths.support] + ([paths.logs] if logs_too else []):
        if path.exists():
            shutil.move(str(path), str(trash / path.name))
            moved.append(path)
    print("Moved to the Trash (%s):" % trash)
    for path in moved:
        print("  %s" % path)
    return 0


def status(paths: Paths, home: Path) -> int:
    loaded = launchctl("print", "gui/%d/%s" % (os.getuid(), AGENT_LABEL)) == 0
    print("Upgrade All %s" % __version__)
    print("  LaunchAgent: %s (%s)" % ("loaded" if loaded else "not loaded", plist_path(home)))
    print("  Settings:    %s" % paths.config)
    print("  Hooks:       %s" % paths.hooks)
    print("  Logs:        %s" % paths.logs)
    try:
        state = json.loads(paths.state.read_text())
        print("  Last run:    %s, %s (exit %s)" % (state["started"], state["outcome"], state["exit_code"]))
        print("  Next run:    about %s" % state.get("next_run", "?"))
        print("  Report:      %s" % state["report_file"])
    except (OSError, ValueError, KeyError):
        print("  Last run:    none yet")
    return 0


def grant_access(paths: Paths, config: Config, step: str = "", wait_seconds: int = 120) -> int:
    """Runs one topgrade step as a launchd job, so macOS asks for access for the CURRENT topgrade.

    From a terminal or an editor the app is the responsible process: macOS does not ask and
    topgrade gets no permission of its own.
    """
    topgrade = shutil.which("topgrade", path=os.environ.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin")
    if not topgrade:
        print("topgrade was not found.")
        return 2
    if not step:
        try:
            step = (json.loads(paths.state.read_text()).get("access_steps") or [config.access_probe_step])[0]
        except (OSError, ValueError):
            step = config.access_probe_step
    paths.logs.mkdir(parents=True, exist_ok=True)
    log = paths.logs / "grant-access.log"
    log.write_text("")
    label = "%s.grant-access.%d" % (AGENT_LABEL, os.getpid())
    print("topgrade: %s" % os.path.realpath(topgrade))
    print("Running the step %r as a background job. If macOS asks, click Allow." % step)
    if launchctl("submit", "-l", label, "-o", str(log), "-e", str(log), "--",
                 topgrade, "--yes", "--no-ask-retry", "--no-self-update", "--only", step) != 0:
        print("launchctl submit failed.")
        return 2
    from . import summary
    verdict = "unclear"
    for _ in range(max(1, wait_seconds // 5)):
        time.sleep(5)
        content = log.read_text(errors="replace")
        steps = summary.steps(content)
        if steps:
            verdict = "denied" if any(summary.outcome(s) == "failed" for _, s in steps) else "ok"
            break
        if summary.access_denied(content):
            verdict = "denied"
            break
    launchctl("remove", label)  # submitted jobs restart when they end; remove it as soon as we know
    if verdict == "ok":
        print("OK: the step works in the background now.")
        return 0
    if verdict == "denied":
        print("Still denied. If macOS showed a question, click Allow and run this again. Otherwise add this file "
              "under System Settings > Privacy & Security > Full Disk Access:\n  %s" % os.path.realpath(topgrade))
        return 1
    print("No result within %d seconds. Log: %s" % (wait_seconds, log))
    return 2
