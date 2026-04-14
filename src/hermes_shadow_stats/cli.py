from __future__ import annotations

import argparse
from pathlib import Path

from .renderer import render_ascii_panel, render_json, render_markdown, render_svg_card
from .scanner import scan_hermes_home
from .stats import build_character_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an RPG-style status panel from a Hermes home directory.")
    parser.add_argument("--hermes-home", default="~/.hermes", help="Path to the Hermes home/profile to scan.")
    parser.add_argument("--name", default="Hermes", help="Character name to display.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "ascii", "svg"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        help="Optional file path for svg/json/markdown/ascii output. If omitted, prints to stdout.",
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
        rendered = render_json(profile)
    elif args.format == "ascii":
        rendered = render_ascii_panel(profile)
    elif args.format == "svg":
        rendered = render_svg_card(profile)
    else:
        rendered = render_markdown(profile)

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(output_path)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
