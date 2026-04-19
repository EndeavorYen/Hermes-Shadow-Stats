"""Phase 6 W6.2 — HERMES_TEAL hex values must match hermes-agent web preset.

Expected values are hard-coded from
``hermes-agent/web/src/themes/presets.ts:11-44`` (``defaultTheme``). The
``color-mix(srgb, ...)`` tokens from the web preset are quantised to their
underlying solid color (alpha dropped) per ``docs/theme-port.md``.
"""

from __future__ import annotations

from hermes_shadow_stats.tui.themes import HERMES_TEAL


# Snapshot of web preset at time of port (see docs/theme-port.md for any
# upstream drift reconciliation procedure).
EXPECTED_HEX = {
    "background": "#041C1C",
    "foreground": "#ffe6cb",
    "accent": "#0c3838",
    "success": "#4ade80",
    "warning": "#ffbd38",
    "danger": "#fb2c36",
    # ``muted`` ports to the web preset's ``muted-foreground`` — the ANSI
    # renderer treats "muted" as a readable low-contrast text color, which
    # aligns with the web's ``muted-foreground`` usage.
    "muted": "#8aaa9a",
}


def test_hermes_teal_name_stable() -> None:
    assert HERMES_TEAL.name == "hermes-teal"


def test_hermes_teal_hex_values_match_web_preset() -> None:
    for field, expected in EXPECTED_HEX.items():
        actual = getattr(HERMES_TEAL, field)
        assert actual.lower() == expected.lower(), (
            f"HERMES_TEAL.{field}: web preset expects {expected!r}, "
            f"port has {actual!r}. Update src/hermes_shadow_stats/tui/themes.py "
            f"or docs/theme-port.md with rationale."
        )
