from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from . import i18n
from .renderer import render_ansi_panel, render_json, render_markdown, render_svg_card
from .scanner import scan_hermes_home
from .stats import build_character_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an RPG-style status panel from a Hermes home directory.")
    parser.add_argument("--hermes-home", default="~/.hermes", help="Path to the Hermes home/profile to scan.")
    parser.add_argument("--name", default="Hermes", help="Character name to display.")
    parser.add_argument(
        "--format",
        choices=("ansi", "markdown", "json", "svg", "ascii"),
        default="ansi",
        help="Output format. ansi is the primary CLI mode.",
    )
    parser.add_argument(
        "--output",
        help="Optional file path for text/json/svg output. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--banner-mode",
        choices=("auto", "wide", "compact", "minimal"),
        default="auto",
        help="Banner/logo mode for ANSI output. auto picks wide/compact/minimal from terminal width.",
    )
    parser.add_argument(
        "--lang",
        choices=i18n.SUPPORTED_LANGS,
        default=None,
        help="Display language. Defaults to $LANG detection then 'en'.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    home = Path(args.hermes_home).expanduser()
    if not home.exists():
        parser.error(f"Hermes home does not exist: {home}")

    lang = i18n.normalize_lang(args.lang) if args.lang else i18n.detect_lang()
    scan = scan_hermes_home(home)
    profile = build_character_profile(scan=scan, name=args.name, lang=lang)

    if args.format == "json":
        rendered = render_json(profile)
    elif args.format in {"ansi", "ascii"}:
        term_columns = shutil.get_terminal_size(fallback=(100, 40)).columns
        panel_width = max(56, min(78, term_columns - 4))
        rendered = render_ansi_panel(profile, banner_mode=args.banner_mode, width=panel_width)
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
