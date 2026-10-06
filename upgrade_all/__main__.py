"""Command line: upgrade-all install | run | status | grant-access | uninstall | sample-report

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, agent, run
from .config import Config, Paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="upgrade-all", description="Simon says: upgrade all! "
                                     "Keeps your Mac up to date with topgrade, unattended, and reports what happened.")
    parser.add_argument("--version", action="version", version="upgrade-all " + __version__)
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="copy the program and set up the background job")
    install.add_argument("--no-agent", action="store_true", help="do not set up the LaunchAgent")
    commands.add_parser("run", help="update now (this is what the background job runs)")
    commands.add_parser("status", help="show the background job and the last run")
    access = commands.add_parser("grant-access", help="let macOS ask again for access for the current topgrade")
    access.add_argument("step", nargs="?", default="", help="topgrade step to run, e.g. skills or node")
    remove = commands.add_parser("uninstall", help="unload the background job and move the program to the Trash")
    remove.add_argument("--logs", action="store_true", help="move logs and reports to the Trash too")
    sample = commands.add_parser("sample-report", help="write a report with made-up data (for screenshots)")
    sample.add_argument("file", type=Path)
    sample.add_argument("--language", default="en")
    args = parser.parse_args(argv)

    paths, home = Paths.default(), Path.home()
    if args.command == "install":
        return agent.install(paths, home, Path(__file__).resolve().parent, with_agent=not args.no_agent)
    if args.command == "run":
        return run.main(paths)
    if args.command == "status":
        return agent.status(paths, home)
    if args.command == "grant-access":
        return agent.grant_access(paths, Config.load(paths.config), args.step)
    if args.command == "uninstall":
        return agent.uninstall(paths, home, logs_too=args.logs)
    if args.command == "sample-report":
        from .sample import write_sample
        write_sample(args.file, args.language)
        print(args.file)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
