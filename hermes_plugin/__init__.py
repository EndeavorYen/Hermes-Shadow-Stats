"""Prototype Hermes plugin wrapper for Hermes Shadow Stats.

Install by copying or symlinking this directory into:

    ~/.hermes/plugins/shadow-stats/

This first prototype intentionally stays lightweight. It does not modify Hermes
core behavior; it only exposes a helper function and a plugin command hook that
can be extended later.
"""

from __future__ import annotations

from pathlib import Path

from hermes_shadow_stats.renderer import render_markdown
from hermes_shadow_stats.scanner import scan_hermes_home
from hermes_shadow_stats.stats import build_character_profile


def _render_for_home(hermes_home: str | Path, name: str = "Hermes") -> str:
    scan = scan_hermes_home(hermes_home)
    profile = build_character_profile(scan=scan, name=name)
    return render_markdown(profile)


def register(ctx) -> None:
    def setup_parser(parser):
        parser.add_argument("--home", default="~/.hermes", help="Hermes home/profile path")
        parser.add_argument("--name", default="Hermes", help="Character name")

    def handler(args):
        return _render_for_home(args.home, name=args.name)

    ctx.register_cli_command(
        name="shadow-stats",
        help="Render an RPG-style Hermes status window",
        setup_fn=setup_parser,
        handler_fn=handler,
        description="Prototype plugin wrapper for Hermes Shadow Stats",
    )
