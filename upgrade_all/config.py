"""Where Upgrade All keeps its files, and its settings.

macOS conventions: program and settings in ~/Library/Application Support/upgrade-all,
logs and reports in ~/Library/Logs/upgrade-all (visible in the Console app).
UPGRADE_ALL_HOME moves everything into one folder (used by the tests).

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

LANGUAGES = ("en", "de", "fr", "it", "es")
AGENT_LABEL = "labs.simon-says.upgrade-all"
EXTRA_PATH = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/local/bin", "/usr/local/sbin"]


@dataclass
class Paths:
    support: Path
    logs: Path

    @classmethod
    def default(cls, env=None) -> "Paths":
        env = os.environ if env is None else env
        if env.get("UPGRADE_ALL_HOME"):
            home = Path(env["UPGRADE_ALL_HOME"])
            return cls(support=home, logs=home / "logs")
        library = Path(env.get("HOME", str(Path.home()))) / "Library"
        return cls(support=library / "Application Support" / "upgrade-all", logs=library / "Logs" / "upgrade-all")

    @property
    def config(self) -> Path:
        return self.support / "config.json"

    @property
    def state(self) -> Path:
        return self.support / "state.json"

    @property
    def hooks(self) -> Path:
        return self.support / "hooks"

    @property
    def app(self) -> Path:
        return self.support / "app"

    @property
    def reports(self) -> Path:
        return self.logs / "reports"

    @property
    def lock(self) -> Path:
        return self.support / "run.lock"


@dataclass
class Config:
    interval_days: float = 3
    language: str = "auto"
    disable_steps: list = field(default_factory=lambda: ["system"])
    cleanup: bool = True
    pre_upgrade_topgrade: bool = True
    restart_outdated_services: bool = True
    retry_failed: bool = True
    retry_delay_seconds: int = 30
    timeout_minutes: float = 180
    open_report: str = "always"          # always | problems | never
    keep_runs: int = 60
    access_probe_step: str = "skills"
    extra_topgrade_args: list = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "Config":
        try:
            raw = json.loads(Path(path).read_text())
        except FileNotFoundError:
            raw = {}
        names = {f.name for f in fields(cls)}
        unknown = sorted(set(raw) - names)
        if unknown:
            raise ValueError("unknown settings in %s: %s" % (path, ", ".join(unknown)))
        config = cls(**raw)
        config.check()
        return config

    def check(self) -> None:
        if self.open_report not in ("always", "problems", "never"):
            raise ValueError("open_report must be always, problems or never")
        if self.language != "auto" and self.language not in LANGUAGES:
            raise ValueError("language must be auto or one of " + ", ".join(LANGUAGES))
        if not 0.04 <= float(self.interval_days) <= 60:
            raise ValueError("interval_days must be between 0.04 (1 hour) and 60")
        if float(self.timeout_minutes) <= 0:
            raise ValueError("timeout_minutes must be positive")
        if int(self.keep_runs) < 1:
            raise ValueError("keep_runs must be at least 1")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2) + "\n")


def system_language(run=subprocess.run, env=None) -> str:
    """First language of macOS ("de-DE" -> "de"), else LANG, else English."""
    env = os.environ if env is None else env
    candidates = []
    try:
        out = run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True, text=True, timeout=5).stdout
        candidates += [part.strip().strip('"') for part in out.strip("()\n ").split(",") if part.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    candidates += [env.get("LC_ALL", ""), env.get("LANG", "")]
    for candidate in candidates:
        code = candidate.lower().replace("_", "-").split("-")[0]
        if code in LANGUAGES:
            return code
    return "en"


def search_path(env=None) -> str:
    """PATH plus the Homebrew folders: launchd starts agents with a minimal PATH.

    The existing PATH comes first, so a user's own choice (and the tests' stand-ins) win.
    """
    env = os.environ if env is None else env
    parts = env.get("PATH", "/usr/bin:/bin").split(":") + EXTRA_PATH + [str(Path(env.get("HOME", "~")) / ".cargo" / "bin")]
    seen, result = set(), []
    for part in parts:
        if part and part not in seen:
            seen.add(part)
            result.append(part)
    return ":".join(result)
