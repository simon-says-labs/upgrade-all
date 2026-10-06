"""Summary parsing, the step table, texts, settings and the LaunchAgent definition.

Run: python3 -m unittest discover -s tests
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from upgrade_all import agent, summary  # noqa: E402
from upgrade_all.config import AGENT_LABEL, Config, Paths, search_path, system_language  # noqa: E402
from upgrade_all.texts import TEXTS  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"

# The hand-made table of the predecessor script (in use since July 2026), label -> --only id.
HAND_TABLE = {
    "Brew (ARM)": "brew_formula", "Brew (Intel)": "brew_formula", "Brew": "brew_formula",
    "Brew Cask (ARM)": "brew_cask", "Brew Cask (Intel)": "brew_cask", "Brew Cask": "brew_cask",
    "Microsoft Office": "microsoft_office", "pipx": "pipx", "Visual Studio Code extensions": "vscode",
    "npm": "node", "Containers": "containers", "GitHub CLI Extensions": "github_cli_extensions",
    "Colima": "colima", "Skills": "skills", "Ollama": "ollama", "pip3": "pip3",
}


class SummaryTest(unittest.TestCase):
    def test_real_german_summary(self):
        steps = summary.steps((FIXTURES / "summary-de.txt").read_text())
        self.assertEqual(len(steps), 11)
        self.assertEqual({summary.outcome(s) for _, s in steps}, {"ok"})

    def test_real_german_failures(self):
        text = (FIXTURES / "summary-de-failed.txt").read_text()
        failed = [l for l, s in summary.steps(text) if summary.outcome(s) == "failed"]
        self.assertEqual(failed, ["npm", "Colima", "Skills"])
        self.assertEqual([summary.step_id(l) for l in failed], ["node", "colima", "skills"])
        self.assertTrue(summary.access_denied(text))

    def test_last_summary_wins_and_colours_are_removed(self):
        text = "―― 1 - Summary ――\nnpm: FAILED\n\x1b[32m―― 2 - Résumé ――\x1b[0m\nnpm: \x1b[32mOK\x1b[0m\n"
        self.assertEqual(summary.steps(text), [("npm", "OK")])

    def test_words_in_other_languages(self):
        for word in ("FAILED", "ÉCHEC", "FALLIDO", "FEHLGESCHLAGEN"):
            self.assertEqual(summary.outcome(word), "failed", word)
        for word in ("SKIPPED", "ÜBERSPRUNGEN", "IGNORÉ", "OMITIDO"):
            self.assertEqual(summary.outcome(word), "skipped", word)

    def test_no_summary(self):
        self.assertEqual(summary.steps("just output\n"), [])


class StepTableTest(unittest.TestCase):
    def test_matches_the_hand_made_table(self):
        self.assertEqual({label: summary.step_id(label) for label in HAND_TABLE}, HAND_TABLE)

    def test_ids_look_like_topgrade_ids(self):
        for label, step in summary.DATA["labels"].items():
            self.assertRegex(step, r"^[a-z][a-z0-9_]*$", label)
        self.assertGreater(len(summary.DATA["labels"]), 150)


class TextsTest(unittest.TestCase):
    def test_every_language_has_every_text_with_the_same_placeholders(self):
        english = TEXTS["en"]
        self.assertEqual(sorted(TEXTS), ["de", "en", "es", "fr", "it"])
        for language, texts in TEXTS.items():
            self.assertEqual(sorted(texts), sorted(english), language)
            for key, value in texts.items():
                self.assertTrue(value.strip(), "%s.%s" % (language, key))
                self.assertEqual(sorted(re.findall(r"\{\d\}", value)), sorted(re.findall(r"\{\d\}", english[key])),
                                 "%s.%s" % (language, key))

    def test_every_text_the_report_uses_exists(self):
        used = set(re.findall(r'\bt\("(\w+)"', (ROOT / "upgrade_all" / "report.py").read_text()))
        used |= {"outcome_ok", "outcome_failed", "outcome_skipped"}
        self.assertEqual(used - set(TEXTS["en"]), set())


class ConfigTest(unittest.TestCase):
    def test_defaults_and_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            self.assertEqual(Config.load(path), Config())
            Config(interval_days=7, language="de").save(path)
            self.assertEqual(Config.load(path).interval_days, 7)

    def test_bad_values(self):
        for bad in ({"language": "nl"}, {"interval_days": 0}, {"keep_runs": 0}, {"timeout_minutes": 0}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    Config(**bad).check()

    def test_paths(self):
        default = Paths.default({"HOME": "/Users/alex"})
        self.assertEqual(str(default.support), "/Users/alex/Library/Application Support/upgrade-all")
        self.assertEqual(str(default.reports), "/Users/alex/Library/Logs/upgrade-all/reports")
        self.assertEqual(Paths.default({"UPGRADE_ALL_HOME": "/tmp/x"}).logs, Path("/tmp/x/logs"))

    def test_search_path_keeps_the_users_order(self):
        path = search_path({"PATH": "/mine:/usr/bin", "HOME": "/Users/alex"}).split(":")
        self.assertEqual(path[:2], ["/mine", "/usr/bin"])
        self.assertIn("/opt/homebrew/bin", path)

    def test_language_from_macos(self):
        class Done:
            stdout = '(\n    "fr-FR",\n    "en-US"\n)\n'
        self.assertEqual(system_language(run=lambda *a, **k: Done(), env={}), "fr")
        self.assertEqual(system_language(run=lambda *a, **k: (_ for _ in ()).throw(OSError()), env={"LANG": "it_IT.UTF-8"}), "it")


class AgentTest(unittest.TestCase):
    def test_launch_agent(self):
        paths = Paths(support=Path("/Users/alex/Library/Application Support/upgrade-all"),
                      logs=Path("/Users/alex/Library/Logs/upgrade-all"))
        plist = agent.agent_plist(paths, Config(interval_days=3))
        self.assertEqual(plist["Label"], AGENT_LABEL)
        self.assertEqual(plist["ProgramArguments"], ["/usr/bin/python3", "-m", "upgrade_all", "run"])
        self.assertEqual(plist["StartInterval"], 259200)
        self.assertFalse(plist["RunAtLoad"])
        self.assertEqual(plist["EnvironmentVariables"]["PYTHONPATH"], str(paths.app))

    def test_install_files_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = Paths(support=root / "support", logs=root / "logs")
            self.assertEqual(agent.install(paths, root, ROOT / "upgrade_all", with_agent=False), 0)
            self.assertTrue((paths.app / "upgrade_all" / "run.py").exists())
            self.assertEqual(json.loads(paths.config.read_text())["interval_days"], 3)
            self.assertTrue((paths.support / "upgrade-all").stat().st_mode & 0o100)
            # a second install keeps the settings and moves the old program copy to the Trash
            Config(interval_days=5).save(paths.config)
            self.assertEqual(agent.install(paths, root, ROOT / "upgrade_all", with_agent=False), 0)
            self.assertEqual(json.loads(paths.config.read_text())["interval_days"], 5)
            self.assertEqual(len(list((root / ".Trash").glob("upgrade-all-app-*"))), 1)


if __name__ == "__main__":
    unittest.main()
