"""Theme presets for the TUI (plan W4.4, audited in Phase 6 W6.2).

Hex values mirror ``hermes-agent/web/src/themes/presets.ts:11-44`` so the TUI
look matches the dashboard. ``color-mix(srgb, ...)`` tokens are quantised to
their solid underlying color (alpha dropped) — see ``docs/theme-port.md``
(Phase 6 deliverable) for the strategy.
"""

from __future__ import annotations

from ..models import ThemePreset


# Source of truth: hermes-agent/web/src/themes/presets.ts (defaultTheme).
HERMES_TEAL: ThemePreset = ThemePreset(
    name="hermes-teal",
    background="#041C1C",
    foreground="#ffe6cb",
    accent="#0c3838",
    success="#4ade80",
    warning="#ffbd38",
    danger="#fb2c36",
    muted="#8aaa9a",
)


_THEMES: dict[str, ThemePreset] = {
    HERMES_TEAL.name: HERMES_TEAL,
}


def available_themes() -> list[str]:
    return sorted(_THEMES)


def get_theme(name: str) -> ThemePreset:
    """Return the preset for ``name``. Raises ``ValueError`` for unknown names.

    The explicit reject path is covered by plan W4.8 (Critic orphan #6) so the
    CLI can surface a clean error instead of silently defaulting.
    """
    try:
        return _THEMES[name]
    except KeyError as err:
        known = ", ".join(available_themes())
        raise ValueError(f"Unknown theme {name!r}. Known themes: {known}") from err
