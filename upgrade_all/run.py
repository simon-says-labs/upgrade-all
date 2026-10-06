"""One unattended update run.

1. Update topgrade itself with Homebrew first. Otherwise the run's Brew step upgrades topgrade and
   `--cleanup` removes the folder of the RUNNING version; later steps that touch protected places
   (for example an external disk) are then denied by macOS.
2. Run topgrade without questions.
3. Restart Homebrew services that still run a version whose folder was just removed.
4. Retry every failed step once with `--only <id>`, after a short pause.
5. Run the extra steps in the hooks folder.
6. Write the log and an HTML report, open it, tidy up old runs.

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import socket
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from . import __version__, summary
from .config import Config, Paths, search_path, system_language

EXIT_OK, EXIT_PROBLEMS, EXIT_SETUP, EXIT_BUSY = 0, 1, 2, 75
HOOK_SKIPPED = 3


class System:
    """Runs programs. Output of `run` goes into a log file, never through a shell."""

    def __init__(self, env=None):
        self.env = dict(os.environ if env is None else env)
        self.env["PATH"] = search_path(self.env)

    def which(self, name: str):
        return shutil.which(name, path=self.env["PATH"])

    def run(self, argv, log: Path, extra_env=None, timeout=None):
        """(exit code, timed out). Appends stdout and stderr to `log`."""
        env = dict(self.env, **(extra_env or {}))
        with open(log, "ab") as out:
            try:
                return subprocess.run(argv, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                      env=env, timeout=timeout).returncode, False
            except subprocess.TimeoutExpired:
                return 124, True
            except OSError as exc:
                out.write(("%s: %s\n" % (argv[0], exc)).encode())
                return 127, False

    def output(self, argv, timeout=60, extra_env=None):
        try:
            done = subprocess.run(argv, capture_output=True, text=True, env=dict(self.env, **(extra_env or {})),
                                  timeout=timeout,
                                  stdin=subprocess.DEVNULL)
            return done.returncode, done.stdout
        except (OSError, subprocess.SubprocessError):
            return 127, ""

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


@dataclass
class StepRow:
    label: str
    status: str
    outcome: str
    retry_status: str = ""
    retry_outcome: str = ""
    retried: bool = False
    known: bool = True


@dataclass
class HookResult:
    name: str
    exit_code: int
    outcome: str
    summary: str = ""
    log_file: str = ""


@dataclass
class RunResult:
    started: str
    finished: str = ""
    seconds: int = 0
    host: str = ""
    language: str = "en"
    upgrade_all: str = __version__
    topgrade_path: str = ""
    version_before: str = ""
    version_after: str = ""
    pre_exit: object = None
    main_exit: int = 0
    timed_out: bool = False
    timeout_minutes: float = 0
    rows: list = field(default_factory=list)
    retried: list = field(default_factory=list)
    fixed: list = field(default_factory=list)
    still_failed: list = field(default_factory=list)
    unknown_failed: list = field(default_factory=list)
    services_restarted: list = field(default_factory=list)
    services_failed: list = field(default_factory=list)
    access_problem: bool = False
    access_steps: list = field(default_factory=list)
    hooks: list = field(default_factory=list)
    log_file: str = ""
    log_display: str = ""
    retry_log_file: str = ""
    report_file: str = ""
    interval_days: float = 3
    outcome: str = "ok"            # ok | fixed | failed
    exit_code: int = 0

    @property
    def hook_problems(self) -> list:
        return [h.name for h in self.hooks if h.outcome == "failed"]


def topgrade_version(system: System, topgrade: str) -> str:
    code, out = system.output([topgrade, "--version"], timeout=30)
    return out.strip().split()[-1] if code == 0 and out.strip() else ""


def outdated_services(system: System, brew: str) -> list:
    """Homebrew services whose process started before the newest installed version appeared."""
    code, listing = system.output(["launchctl", "list"])
    if code != 0:
        return []
    found = []
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) != 3 or not parts[0].isdigit():
            continue
        match = re.match(r"^(?:homebrew\.mxcl|sh\.brew)\.(.+)$", parts[2])
        if not match:
            continue
        name, pid = match.group(1), parts[0]
        code, started = system.output(["ps", "-o", "lstart=", "-p", pid], extra_env={"LC_ALL": "C"})
        code2, cellar = system.output([brew, "--cellar", name])
        if code or code2 or not started.strip() or not cellar.strip():
            continue
        try:
            started_at = datetime.strptime(" ".join(started.split()), "%a %b %d %H:%M:%S %Y")
            versions = [p for p in Path(cellar.strip()).iterdir() if p.is_dir()]
        except (ValueError, OSError):
            continue
        if versions and started_at.timestamp() < max(p.stat().st_mtime for p in versions):
            found.append(name)
    return found


def run_hooks(system: System, paths: Paths, stamp: str, language: str) -> list:
    results = []
    if not paths.hooks.is_dir():
        return results
    for hook in sorted(paths.hooks.iterdir()):
        if hook.name.startswith(".") or not hook.is_file() or not os.access(hook, os.X_OK):
            continue
        log = paths.logs / ("%s_hook_%s.log" % (stamp, re.sub(r"[^\w.-]", "_", hook.name)))
        code, timed_out = system.run([str(hook)], log, {"UPGRADE_ALL_LANGUAGE": language,
                                                        "UPGRADE_ALL_LOGS": str(paths.logs)}, timeout=3600)
        text = log.read_text(errors="replace") if log.exists() else ""
        lines = [l[len("Summary:"):].strip() for l in summary.clean(text).splitlines() if l.startswith("Summary:")]
        outcome = "ok" if code == 0 else "skipped" if code == HOOK_SKIPPED else "failed"
        results.append(HookResult(hook.name, code, outcome, lines[-1] if lines else "", str(log)))
    return results


def to_trash(files, home: Path) -> None:
    """Moves old runs to the Trash instead of deleting them."""
    trash = home / ".Trash"
    if not files or not trash.is_dir():
        return
    target = trash / ("upgrade-all-%s" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    target.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.move(str(path), str(target / path.name))


def tidy_up(paths: Paths, keep_runs: int, home: Path) -> None:
    stamps = sorted({p.name[:19] for p in paths.reports.glob("????-??-??_??-??-??*.html")}, reverse=True)
    old = set(stamps[keep_runs:])
    files = [p for folder in (paths.logs, paths.reports) for p in folder.glob("????-??-??_??-??-??*")
             if p.is_file() and p.name[:19] in old]
    to_trash(files, home)


def update(config: Config, paths: Paths, system: System, now=datetime.now) -> RunResult:
    from . import report  # late import keeps run.py importable without the report's size

    paths.logs.mkdir(parents=True, exist_ok=True)
    paths.reports.mkdir(parents=True, exist_ok=True)
    started = now()
    stamp = started.strftime("%Y-%m-%d_%H-%M-%S")
    language = system_language(env=system.env) if config.language == "auto" else config.language
    result = RunResult(started=started.isoformat(timespec="seconds"), host=socket.gethostname().split(".")[0],
                       language=language, interval_days=config.interval_days, timeout_minutes=config.timeout_minutes)
    log = paths.logs / ("%s.log" % stamp)
    log.touch()
    result.log_file = str(log)

    topgrade, brew = system.which("topgrade"), system.which("brew")
    if not topgrade:
        log.write_text("topgrade was not found in %s\n" % system.env["PATH"])
        result.outcome, result.exit_code, result.main_exit = "failed", EXIT_SETUP, 127
        return finish(result, config, paths, system, report, now)
    result.topgrade_path = os.path.realpath(topgrade)
    result.version_before = topgrade_version(system, topgrade)

    # 1. topgrade first
    if config.pre_upgrade_topgrade and brew and system.output([brew, "list", "--versions", "topgrade"])[0] == 0:
        with open(log, "a") as out:
            out.write("―― upgrade-all: brew upgrade topgrade ――\n")
        result.pre_exit, _ = system.run([brew, "upgrade", "topgrade"], log, timeout=900)
    result.version_after = topgrade_version(system, topgrade) or result.version_before
    result.topgrade_path = os.path.realpath(topgrade)

    # 2. main run
    args = [topgrade, "--yes", "--no-ask-retry", "--no-self-update"]
    if config.cleanup:
        args.append("--cleanup")
    if config.disable_steps:
        args += ["--disable"] + list(config.disable_steps)
    args += list(config.extra_topgrade_args)
    with open(log, "a") as out:
        out.write("\n―― upgrade-all: %s ――\n" % " ".join(args))
    result.main_exit, result.timed_out = system.run(args, log, {"NO_COLOR": "1"}, timeout=float(config.timeout_minutes) * 60)

    # 3. services that still run a removed version
    if config.restart_outdated_services and brew:
        for name in outdated_services(system, brew):
            with open(log, "a") as out:
                out.write("\n―― upgrade-all: brew services restart %s ――\n" % name)
            code, _ = system.run([brew, "services", "restart", name], log, timeout=300)
            (result.services_restarted if code == 0 else result.services_failed).append(name)
        if result.services_restarted:
            system.sleep(10)

    # 4. retry failed steps once
    main_steps = summary.steps(log.read_text(errors="replace"))
    failed = [label for label, status in main_steps if summary.outcome(status) == "failed"]
    ids = []
    for label in failed:
        step = summary.step_id(label)
        if step and step not in ids:
            ids.append(step)
        elif not step:
            result.unknown_failed.append(label)
    retry_steps = {}
    retry_text = ""
    if config.retry_failed and ids and not result.timed_out:
        system.sleep(config.retry_delay_seconds)
        retry_log = paths.logs / ("%s_retry.log" % stamp)
        retry_log.touch()
        result.retry_log_file = str(retry_log)
        system.run([topgrade, "--yes", "--no-ask-retry", "--no-self-update", "--only"] + ids, retry_log,
                   {"NO_COLOR": "1"}, timeout=float(config.timeout_minutes) * 60)
        retry_text = retry_log.read_text(errors="replace")
        retry_steps = dict(summary.steps(retry_text))
        result.retried = [label for label in failed if summary.step_id(label)]

    for label, status in main_steps:
        row = StepRow(label, status, summary.outcome(status), known=summary.step_id(label) is not None)
        if row.outcome == "failed" and label in retry_steps:
            row.retried, row.retry_status = True, retry_steps[label]
            row.retry_outcome = summary.outcome(row.retry_status)
        result.rows.append(row)
        if row.outcome == "failed":
            (result.fixed if row.retry_outcome == "ok" else result.still_failed).append(label)

    still_failing_text = retry_text if result.retried else log.read_text(errors="replace")
    if result.still_failed and summary.access_denied(still_failing_text):
        result.access_problem = True
        result.access_steps = [summary.step_id(l) for l in result.still_failed if summary.step_id(l)]

    # 5. extra steps
    result.hooks = run_hooks(system, paths, stamp, language)

    if result.main_exit == 0 and not result.timed_out:
        result.outcome = "ok"
    elif failed and not result.still_failed and not result.timed_out:
        result.outcome = "fixed"
    else:
        result.outcome = "failed"
    result.exit_code = EXIT_PROBLEMS if result.outcome == "failed" else EXIT_OK
    return finish(result, config, paths, system, report, now)


def finish(result: RunResult, config: Config, paths: Paths, system: System, report, now) -> RunResult:
    finished = now()
    result.finished = finished.isoformat(timespec="seconds")
    result.seconds = int((finished - datetime.fromisoformat(result.started)).total_seconds())
    stamp = datetime.fromisoformat(result.started).strftime("%Y-%m-%d_%H-%M-%S")
    report_file = paths.reports / ("%s.html" % stamp)
    report_file.write_text(report.render(result), encoding="utf-8")
    result.report_file = str(report_file)
    state = asdict(result)
    state["next_run"] = (finished + timedelta(days=float(config.interval_days))).isoformat(timespec="minutes")
    paths.state.parent.mkdir(parents=True, exist_ok=True)
    paths.state.write_text(json.dumps(state, indent=1))
    problems = result.outcome == "failed" or bool(result.hook_problems)
    if config.open_report == "always" or (config.open_report == "problems" and problems):
        system.output(["open", str(report_file)])
    tidy_up(paths, int(config.keep_runs), Path(system.env.get("HOME", str(Path.home()))))
    return result


def main(paths: Paths, system: System = None) -> int:
    system = system or System()
    try:
        config = Config.load(paths.config)
    except (ValueError, TypeError) as exc:
        print("Upgrade All: %s" % exc)
        return EXIT_SETUP
    paths.support.mkdir(parents=True, exist_ok=True)
    with open(paths.lock, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("Upgrade All: another run is still in progress.")
            return EXIT_BUSY
        result = update(config, paths, system)
    print("Upgrade All: %s (exit %d). Report: %s" % (result.outcome, result.exit_code, result.report_file))
    return result.exit_code
