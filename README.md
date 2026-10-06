<p align="center"><img src="docs/logo.png" width="250" alt="Upgrade All logo"></p>

# Upgrade All

**Simon says: upgrade all!** Keeps your Mac up to date with [topgrade](https://github.com/topgrade-rs/topgrade),
unattended, every few days, and tells you in a clear report what happened. When a step fails, Upgrade All tries
to fix it by itself before it bothers you.

> **Kurz auf Deutsch:** Upgrade All hält deinen Mac mit topgrade im Hintergrund aktuell (Homebrew, Apps,
> npm, pipx, VS-Code-Erweiterungen und alles, was topgrade kennt) und zeigt danach einen Bericht. Schlägt ein
> Schritt fehl, wird er einmal automatisch wiederholt. Eigene Zusatzschritte hängst du als Hook an. Bericht auf
> Deutsch, Englisch, Französisch, Italienisch und Spanisch.

<p align="center"><img src="docs/report-light.png" width="760" alt="Report of a run: your Mac is up to date, errors were fixed automatically. npm failed at first and succeeded on the retry; topgrade was updated first and a Homebrew service was restarted."></p>

## What a run does

1. **Updates topgrade first.** Otherwise the run's Homebrew step updates topgrade itself and `--cleanup` removes
   the folder of the version that is still running. Later steps that touch protected places (for example an
   external disk) are then denied by macOS, with misleading messages.
2. **Runs topgrade without questions** (`--yes --no-ask-retry --no-self-update --cleanup`, macOS system updates
   left out because they ask for a password).
3. **Restarts Homebrew services** that still run a version whose folder was just removed.
4. **Retries every failed step once**, after a short pause, with exactly that step (`topgrade --only <step>`).
   The step names come from topgrade's own source, so the summary is understood in every language topgrade
   speaks.
5. **Runs your extra steps** from the hooks folder.
6. **Writes a report** and opens it in your browser (always, only on problems, or never). Old runs go to the
   Trash after a while; nothing is deleted.

## Install

Needs macOS, [Homebrew](https://brew.sh) and topgrade (`brew install topgrade`). Upgrade All itself has no
dependencies: it runs on `/usr/bin/python3`, which comes with Apple's Command Line Tools. The Homebrew installer
sets them up; otherwise `xcode-select --install`.

```bash
git clone https://github.com/simon-says-labs/upgrade-all
cd upgrade-all
/usr/bin/python3 -m upgrade_all install
```

This copies the program to `~/Library/Application Support/upgrade-all/` and sets up the background job
`labs.simon-says.upgrade-all` (every 3 days). Try it right away:

```bash
~/Library/Application\ Support/upgrade-all/upgrade-all run
```

## Commands

| Command | Does |
|---|---|
| `upgrade-all run` | Update now (this is what the background job runs). |
| `upgrade-all status` | Background job, last run, next run, last report. |
| `upgrade-all grant-access [step]` | Lets macOS ask again for access for the current topgrade (see below). |
| `upgrade-all install` | Install or update; keeps your settings. `--no-agent` skips the background job. |
| `upgrade-all uninstall` | Unloads the background job and moves the program to the Trash. `--logs` moves the logs too. |

## Settings

`~/Library/Application Support/upgrade-all/config.json`:

| Setting | Default | Meaning |
|---|---|---|
| `interval_days` | `3` | Days between runs. Run `install` again after changing it. |
| `language` | `auto` | Report language: `auto` (macOS language), `en`, `de`, `fr`, `it`, `es`. |
| `disable_steps` | `["system"]` | topgrade steps to leave out, e.g. `["system", "uv"]`. |
| `cleanup` | `true` | Remove old versions after updating (`--cleanup`). |
| `pre_upgrade_topgrade` | `true` | Update topgrade with Homebrew before the run. |
| `restart_outdated_services` | `true` | Restart Homebrew services that still run a removed version. |
| `retry_failed` | `true` | Retry failed steps once. |
| `retry_delay_seconds` | `30` | Pause before the retry. |
| `timeout_minutes` | `180` | Stop topgrade if it takes longer. |
| `open_report` | `always` | `always`, `problems` or `never`. |
| `keep_runs` | `60` | Runs to keep; older logs and reports go to the Trash. |
| `access_probe_step` | `skills` | Step `grant-access` uses when the last run named none. |
| `extra_topgrade_args` | `[]` | More arguments for topgrade, e.g. `["--disable", "containers"]`. |

## Extra steps (hooks)

Put executable files into `~/Library/Application Support/upgrade-all/hooks/`. They run after topgrade, in name
order. Exit code `0` means OK, `3` skipped, anything else failed. A line starting with `Summary:` appears in the
report. `UPGRADE_ALL_LANGUAGE` and `UPGRADE_ALL_LOGS` are set. An extra step never changes topgrade's result.
See [examples/hooks](examples/hooks) for one that keeps a Brewfile of everything installed.

## When macOS denies access

macOS remembers some permissions, such as access to files on an external disk, **per program file**. topgrade's
file path contains its version, so every topgrade update starts without that permission, and from a terminal
macOS never asks for it: there the terminal app is responsible, not topgrade. If a step is still denied after
the retry, the report says so and names the command:

```bash
upgrade-all grant-access skills
```

It runs that one step as a background job, the way the scheduled run does, so macOS asks; click **Allow**.

## Development

```bash
/usr/bin/python3 -m unittest discover -s tests       # stand-ins for topgrade and brew, nothing is updated
/usr/bin/python3 -m upgrade_all sample-report /tmp/report.html --language de
/usr/bin/python3 tools/update_steps.py v17.12.3       # refresh the step table from topgrade's source
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes: [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE) © 2026 Simon Eckmiller · published by [Simon Says](https://github.com/simon-says-labs).
Third-party parts: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Upgrade All is an independent project and not
part of topgrade.
