# Changelog

All notable changes to Upgrade All. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [Semantic Versioning](https://semver.org/).

## 1.0.0 - 2026-10-06

First public release. Grew out of a personal script that has kept a Mac up to date every three days since
July 2026.

- Unattended topgrade run as a LaunchAgent, with configurable interval.
- Self-correction: topgrade is updated before the run, Homebrew services that still run a removed version are
  restarted, and every failed step is retried once with `--only`.
- Step table built from topgrade's source (`tools/update_steps.py`); the summary is understood in every language
  topgrade prints it in.
- Extra steps as hooks, with OK / skipped / failed and a summary line in the report.
- Self-contained HTML report in English, German, French, Italian and Spanish, light and dark.
- `grant-access` to let macOS ask again for access for a new topgrade version.
- Old runs go to the Trash, never deleted; `uninstall` moves the program to the Trash.
