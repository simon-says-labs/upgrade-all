# Third-party notices

Upgrade All is MIT licensed (see [LICENSE](LICENSE)). It runs [topgrade](https://github.com/topgrade-rs/topgrade)
(GPL-3.0) as a separate program and does not contain its code.

`upgrade_all/data/steps.json` lists topgrade's step names, step ids and the translations of a few summary words
(Summary, OK, FAILED, SKIPPED, IGNORED). `tools/update_steps.py` reads them from topgrade's `src/step.rs` and
`locales/app.yml` (topgrade 17.12.3) so that Upgrade All can understand topgrade's summary.
