from __future__ import annotations

import argparse
from pathlib import Path

from .renderer import render_ascii_panel, render_json, render_markdown
from .scanner import scan_hermes_home
from .stats import build_character_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an RPG-style status panel from a Hermes home directory.")
    parser.add_argument("--hermes-home", default="~/.hermes", help="Path to the Hermes home/profile to scan.")
    parser.add_argument("--name", default="Hermes", help="Character name to display.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "ascii"),
        default="markdown",
        help="Output format.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    home = Path(args.hermes_home).expanduser()
    if not home.exists():
        parser.error(f"Hermes home does not exist: {home}")

    scan = scan_hermes_home(home)
    profile = build_character_profile(scan=scan, name=args.name)

    if args.format == "json":
        print(render_json(profile))
    elif args.format == "ascii":
        print(render_ascii_panel(profile))
    else:
        print(render_markdown(profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
