# Contributing

Thanks for your interest in Upgrade All. Bug reports, ideas and pull requests are welcome.

## Reporting a bug

Open an [issue](https://github.com/simon-says-labs/upgrade-all/issues) with your macOS and topgrade versions
(`topgrade --version`), what you expected and what happened, and the summary part of the log from
`~/Library/Logs/upgrade-all/`. Please remove paths or names you do not want to share.

## Development

No real update ever runs in the tests: `tests/fakes/` holds stand-ins for topgrade, brew, launchctl, ps and
open, and every test checks that the stand-in is used.

```bash
/usr/bin/python3 -m unittest discover -s tests
/usr/bin/python3 -m upgrade_all sample-report /tmp/report.html --language fr
```

| File | Does |
|---|---|
| `upgrade_all/run.py` | one run: update topgrade, run it, restart services, retry, hooks, report |
| `upgrade_all/summary.py` | reads topgrade's summary in any language |
| `upgrade_all/report.py`, `texts.py` | the HTML report and its texts |
| `upgrade_all/agent.py` | install, uninstall, status, grant-access |
| `tools/update_steps.py` | rebuilds `data/steps.json` from a topgrade release |

## Pull requests

- One topic per pull request, with a test that fails without your change.
- Report texts need all five languages in `texts.py`; the tests check it.
- Stay compatible with Python 3.9 (`/usr/bin/python3` on macOS) and the standard library.
- Add a line to `CHANGELOG.md` under an `Unreleased` heading.
