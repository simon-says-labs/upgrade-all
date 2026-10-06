"""Whole runs against stand-ins for topgrade, brew, launchctl, ps and open (tests/fakes).

No real topgrade or Homebrew is touched: the stand-ins come first in PATH, and every test
checks that the resolved topgrade is the stand-in.

Run: python3 -m unittest discover -s tests
"""
import fcntl
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from upgrade_all import run  # noqa: E402
from upgrade_all.config import Config, Paths  # noqa: E402

FAKES = ROOT / "tests" / "fakes"

class FastSystem(run.System):
    """No real waiting between steps."""

    def sleep(self, seconds):
        pass


ALL_OK = [["Brew (ARM)", "OK"], ["Brew Cask (ARM)", "OK"], ["npm", "OK"], ["Skills", "OK"]]


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="upgrade-all-test-"))
        (self.tmp / "home" / ".Trash").mkdir(parents=True)
        self.paths = Paths(support=self.tmp / "support", logs=self.tmp / "logs")
        self.calls = self.tmp / "calls.jsonl"
        self.env = {"PATH": "%s:/usr/bin:/bin" % FAKES, "HOME": str(self.tmp / "home"),
                    "FAKE_PLAN": str(self.tmp / "plan.json"), "FAKE_CALLS": str(self.calls),
                    "FAKE_VERSION_FILE": str(self.tmp / "version"), "FAKE_CELLAR": str(self.tmp / "cellar")}
        self.config = Config(language="en", retry_delay_seconds=0, open_report="never")

    def go(self, plan, config=None):
        (self.tmp / "plan.json").write_text(json.dumps(plan))
        system = FastSystem(self.env)
        self.assertEqual(Path(system.which("topgrade")).parent, FAKES)  # never the real topgrade
        result = run.update(config or self.config, self.paths, system)
        self.report = Path(result.report_file).read_text()
        return result

    def call_list(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def test_clean_run(self):
        result = self.go({"main": {"exit": 0, "summary": ALL_OK}})
        self.assertEqual((result.outcome, result.exit_code), ("ok", 0))
        calls = self.call_list()
        upgrade = calls.index(["brew", "upgrade", "topgrade"])
        main = next(i for i, c in enumerate(calls) if c[:2] == ["topgrade", "--yes"])
        self.assertLess(upgrade, main)  # topgrade is updated BEFORE the run
        self.assertEqual(calls[main], ["topgrade", "--yes", "--no-ask-retry", "--no-self-update", "--cleanup",
                                       "--disable", "system"])
        self.assertIn("Your Mac is up to date.", self.report)
        self.assertEqual(len(result.rows), 4)
        state = json.loads(self.paths.state.read_text())
        self.assertEqual((state["outcome"], state["exit_code"]), ("ok", 0))

    def test_failed_step_fixed_by_retry(self):
        result = self.go({"main": {"exit": 1, "summary": [["Brew (ARM)", "OK"], ["npm", "FAILED"]]},
                          "retry": {"exit": 0, "summary": [["npm", "OK"]]}})
        self.assertEqual((result.outcome, result.exit_code, result.fixed), ("fixed", 0, ["npm"]))
        self.assertIn(["topgrade", "--yes", "--no-ask-retry", "--no-self-update", "--only", "node"], self.call_list())
        self.assertIn("fixed by the automatic retry: npm", self.report)

    def test_still_failing_with_access_problem(self):
        result = self.go({"main": {"exit": 1, "summary": [["Skills", "FAILED"]]},
                          "retry": {"exit": 1, "text": "npm ERR! code EPERM", "summary": [["Skills", "FAILED"]]}})
        self.assertEqual((result.outcome, result.exit_code, result.still_failed), ("failed", 1, ["Skills"]))
        self.assertTrue(result.access_problem)
        self.assertIn("upgrade-all grant-access skills", self.report)
        self.assertEqual(json.loads(self.paths.state.read_text())["access_steps"], ["skills"])

    def test_german_summary_is_understood(self):
        result = self.go({"heading": "Zusammenfassung",
                          "main": {"exit": 1, "summary": [["Ollama", "FEHLGESCHLAGEN"], ["pipx", "OK"]]},
                          "retry": {"exit": 0, "summary": [["Ollama", "OK"]]}})
        self.assertEqual((result.outcome, result.fixed), ("fixed", ["Ollama"]))

    def test_unknown_step_is_not_guessed(self):
        result = self.go({"main": {"exit": 1, "summary": [["Something new", "FAILED"]]}})
        self.assertEqual((result.outcome, result.unknown_failed), ("failed", ["Something new"]))
        self.assertFalse(any("--only" in c for c in self.call_list()))

    def test_run_without_summary(self):
        result = self.go({"main": {"exit": 1, "summary": None, "text": "panicked at src/main.rs"}})
        self.assertEqual(result.outcome, "failed")
        self.assertIn("printed no summary", self.report)

    def test_timeout(self):
        config = Config(language="en", retry_delay_seconds=0, open_report="never", timeout_minutes=0.02)
        result = self.go({"main": {"exit": 0, "sleep": 5, "summary": ALL_OK}}, config)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, 1)

    def test_log_content_is_escaped(self):
        self.go({"main": {"exit": 0, "text": "<script>alert(1)</script> & <b>",
                          "summary": ALL_OK + [["<img src=x onerror=alert(2)>", "OK"]]}})
        self.assertNotIn("<script>alert", self.report)
        self.assertNotIn("<img src=x", self.report)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; &lt;b&gt;", self.report)

    def test_topgrade_updated_first_is_reported(self):
        self.go({"upgrade_to": "17.12.4", "main": {"exit": 0, "summary": ALL_OK}})
        self.assertIn("17.12.3 → 17.12.4", self.report)

    def test_pre_upgrade_can_be_turned_off(self):
        config = Config(language="en", retry_delay_seconds=0, open_report="never", pre_upgrade_topgrade=False)
        self.go({"main": {"exit": 0, "summary": ALL_OK}}, config)
        self.assertNotIn(["brew", "upgrade", "topgrade"], self.call_list())

    def test_outdated_service_is_restarted(self):
        version = self.tmp / "cellar" / "ollama" / "0.34.3"
        version.mkdir(parents=True)
        result = self.go({"main": {"exit": 0, "summary": ALL_OK}, "services": [["4242", "sh.brew.ollama"],
                          ["4343", "homebrew.mxcl.redis"]], "started": {"4242": "Mon Jan  5 08:00:00 2026"}})
        self.assertEqual(result.services_restarted, ["ollama"])  # redis has no cellar folder
        self.assertIn(["brew", "services", "restart", "ollama"], self.call_list())

    def test_hooks(self):
        self.paths.hooks.mkdir(parents=True)
        hooks = {"10-ok": "echo working; echo Summary: 3 updated", "20-skip": "exit 3",
                 "30-fail": "echo broken; exit 5", "40-lang": "echo Summary: $UPGRADE_ALL_LANGUAGE"}
        for name, body in hooks.items():
            hook = self.paths.hooks / name
            hook.write_text("#!/bin/sh\n%s\n" % body)
            hook.chmod(0o755)
        (self.paths.hooks / "README.txt").write_text("not executable, ignored")
        result = self.go({"main": {"exit": 0, "summary": ALL_OK}})
        self.assertEqual([(h.name, h.outcome, h.summary) for h in result.hooks],
                         [("10-ok", "ok", "3 updated"), ("20-skip", "skipped", ""), ("30-fail", "failed", ""),
                          ("40-lang", "ok", "en")])
        self.assertEqual(result.exit_code, 0)  # extra steps never change topgrade's result
        self.assertIn("Extra steps with problems: 30-fail.", self.report)

    def test_open_report_on_problems_only(self):
        config = Config(language="en", retry_delay_seconds=0, open_report="problems")
        self.go({"main": {"exit": 0, "summary": ALL_OK}}, config)
        self.assertFalse(Path(str(self.calls) + ".open").exists())
        self.go({"main": {"exit": 1, "summary": [["Something new", "FAILED"]]}}, config)
        self.assertTrue(Path(str(self.calls) + ".open").exists())

    def test_old_runs_go_to_the_trash(self):
        config = Config(language="en", retry_delay_seconds=0, open_report="never", keep_runs=1)
        clock = iter(["2026-10-01T08:00:00", "2026-10-01T08:00:05", "2026-10-04T08:00:00", "2026-10-04T08:00:05"])
        from datetime import datetime
        (self.tmp / "plan.json").write_text(json.dumps({"main": {"exit": 0, "summary": ALL_OK}}))
        system = FastSystem(self.env)
        for _ in range(2):
            run.update(config, self.paths, system, now=lambda: datetime.fromisoformat(next(clock)))
        self.assertEqual([p.name for p in self.paths.reports.iterdir()], ["2026-10-04_08-00-00.html"])
        trashed = [p.name for p in (self.tmp / "home" / ".Trash").rglob("2026-10-01*")]
        self.assertEqual(sorted(trashed), ["2026-10-01_08-00-00.html", "2026-10-01_08-00-00.log"])

    def test_second_run_waits_for_the_first(self):
        self.paths.support.mkdir(parents=True)
        with open(self.paths.lock, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.assertEqual(run.main(self.paths, FastSystem(self.env)), run.EXIT_BUSY)

    def test_broken_settings(self):
        self.paths.support.mkdir(parents=True)
        self.paths.config.write_text(json.dumps({"open_report": "sometimes"}))
        self.assertEqual(run.main(self.paths, FastSystem(self.env)), run.EXIT_SETUP)
        self.paths.config.write_text(json.dumps({"colour": "blue"}))
        self.assertEqual(run.main(self.paths, FastSystem(self.env)), run.EXIT_SETUP)

    def test_missing_topgrade(self):
        env = dict(self.env, PATH="/usr/bin:/bin")
        (self.tmp / "plan.json").write_text("{}")
        system = FastSystem(env)
        if system.which("topgrade"):
            self.skipTest("a real topgrade is installed in a system folder")
        result = run.update(self.config, self.paths, system)
        self.assertEqual((result.outcome, result.exit_code), ("failed", run.EXIT_SETUP))


if __name__ == "__main__":
    unittest.main()
