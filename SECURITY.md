# Security policy

Only the latest release receives fixes. Please report vulnerabilities through
[GitHub's private vulnerability reporting](https://github.com/simon-says-labs/upgrade-all/security/advisories/new),
not in public issues.

## What Upgrade All does on your Mac

- It runs as your user, never with `sudo`. topgrade's `system` step (macOS updates, which needs a password) is
  left out by default.
- It runs topgrade, Homebrew (`brew upgrade topgrade`, `brew services restart`) and the hooks **you** put into the
  hooks folder. Anything in that folder runs with your rights, so only add scripts you trust.
- Programs are called directly, never through a shell; log content is escaped before it goes into the report.
  The report is a local file without scripts and makes no network requests.
- `grant-access` only starts one topgrade step as a background job so that macOS can ask you; it cannot grant
  anything by itself.
- Nothing is deleted: old runs and an uninstalled program go to the Trash.
