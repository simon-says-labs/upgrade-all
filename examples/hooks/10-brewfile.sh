#!/bin/sh
# An extra step for Upgrade All: after each run, write a Brewfile of everything Homebrew has installed,
# so a new Mac can be set up the same way (brew bundle install --file ~/Brewfile).
#
# Copy it to ~/Library/Application Support/upgrade-all/hooks/ and make it executable (chmod +x).
# Hooks run after topgrade, in name order.
#
#   exit 0  OK
#   exit 3  skipped (for example: nothing to do right now)
#   other   failed
#
# The last line starting with "Summary:" appears in the report.
# UPGRADE_ALL_LANGUAGE (en, de, fr, it, es) and UPGRADE_ALL_LOGS are set.

if ! command -v brew >/dev/null 2>&1; then
  echo "Summary: Homebrew not found"
  exit 3
fi
brew bundle dump --file="$HOME/Brewfile" --force || exit 1
echo "Summary: $(grep -c . "$HOME/Brewfile") entries in ~/Brewfile"
