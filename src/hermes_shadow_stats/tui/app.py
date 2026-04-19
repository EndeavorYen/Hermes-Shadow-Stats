"""Shadow Stats Textual shell (plan Phase 4).

Creates a ``ShadowStatsApp`` with 8 tabbed panes, each rendering its per-tab
ANSI string via the Phase-0-chosen primitive ``Static(Text.from_ansi(s))``.

The App is deliberately thin:
- Data-acquisition (state.db reader + scanner) lives outside the widget tree
  so perf tests can measure acquisition time without a running event loop.
- Detail drill-in is stubbed here for Phase 5; the shell already carries the
  Enter/Esc bindings so Phase 5 can wire them without touching keymap.py.
"""

from __future__ import annotations

import os
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from .. import i18n
from ..models import CharacterProfile, ThemePreset
from ..renderer import TAB_IDS, render_tab
from ..scanner import scan_hermes_home
from ..state_db import load_telemetry
from ..stats import build_character_profile
from .keymap import SHELL_BINDINGS
from .themes import HERMES_TEAL, get_theme
from .widgets.detail import DetailScreen, is_detail_capable
from .widgets.help_overlay import HelpScreen


def load_profile(
    hermes_home: str | Path,
    *,
    name: str = "Hermes",
    lang: str = "en",
    use_state_db: bool = True,
) -> CharacterProfile:
    """Build a full ``CharacterProfile`` from disk.

    Kept module-level (not a method) so ``tests/test_data_acquisition_perf.py``
    can time it without mounting the TUI.
    """
    home = Path(hermes_home).expanduser()
    scan = scan_hermes_home(home)
    if use_state_db:
        telemetry, reason = load_telemetry(home)
    else:
        telemetry, reason = None, "no-state-db"
    return build_character_profile(
        scan=scan,
        name=name,
        lang=lang,
        telemetry=telemetry,
        fallback_reason=reason,
    )


class ShadowStatsApp(App):
    """Textual app rendering the 8 RPG tabs over a CharacterProfile snapshot."""

    CSS = """
    Screen {
        background: $background;
    }
    .tab-body {
        padding: 0 1;
    }
    """

    BINDINGS = SHELL_BINDINGS
    TITLE = "Hermes Shadow Stats"

    def __init__(
        self,
        profile: CharacterProfile,
        *,
        lang: str | None = None,
        theme: ThemePreset | None = None,
        tab_width: int = 78,
    ) -> None:
        super().__init__()
        self._profile = profile
        self._lang = i18n.normalize_lang(lang or profile.lang)
        self._theme_preset = theme or HERMES_TEAL
        self._tab_width = tab_width
        # Keeps the original hermes_home so ``action_refresh_snapshot`` can
        # re-run the data-acquisition pipeline (plan W6.7).
        self._hermes_home: Path | None = Path(profile.scan.hermes_home)

    # ---------------------------------------------------------------- compose

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with TabbedContent(id="main-tabs"):
            for tab_id in TAB_IDS:
                title = i18n.t_label(self._lang, f"tab_{tab_id}")
                with TabPane(title, id=f"pane-{tab_id}"):
                    yield Container(
                        Static(
                            self._render_tab(tab_id),
                            id=f"content-{tab_id}",
                            markup=False,
                        ),
                        classes="tab-body",
                    )
        yield Footer()

    def on_mount(self) -> None:
        # Apply theme color tokens into Textual's CSS variables. Keeps the
        # preset the single source of truth (HERMES_TEAL hex values).
        preset = self._theme_preset
        self.screen.styles.background = preset.background
        self.screen.styles.color = preset.foreground

    # ---------------------------------------------------------------- helpers

    def _render_tab(self, tab_id: str) -> Text:
        """Render a tab string and wrap it via the Phase-0 primitive."""
        rendered = render_tab(
            tab_id,
            self._profile,
            width=self._tab_width,
            lang=self._lang,
            telemetry=self._profile.telemetry,
        )
        return Text.from_ansi(rendered)

    def _current_tab_index(self) -> int:
        tabs = self.query_one(TabbedContent)
        active = tabs.active
        # active is the id of the currently visible TabPane (e.g. "pane-status").
        try:
            return TAB_IDS.index(active.removeprefix("pane-"))
        except ValueError:
            return 0

    # ---------------------------------------------------------------- actions

    def action_next_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        idx = (self._current_tab_index() + 1) % len(TAB_IDS)
        tabs.active = f"pane-{TAB_IDS[idx]}"

    def action_previous_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        idx = (self._current_tab_index() - 1) % len(TAB_IDS)
        tabs.active = f"pane-{TAB_IDS[idx]}"

    def action_switch_tab(self, index: int) -> None:
        if 0 <= index < len(TAB_IDS):
            self.query_one(TabbedContent).active = f"pane-{TAB_IDS[index]}"

    def action_refresh_snapshot(self) -> None:
        """Re-run data acquisition and re-render all 8 tabs (plan W6.7)."""
        if self._hermes_home is None:
            return
        use_state_db = os.environ.get("HERMES_SHADOW_STATS_NO_STATE_DB") != "1"
        self._profile = load_profile(
            self._hermes_home,
            name=self._profile.name,
            lang=self._lang,
            use_state_db=use_state_db,
        )
        for tab_id in TAB_IDS:
            widget = self.query_one(f"#content-{tab_id}", Static)
            widget.update(self._render_tab(tab_id))

    def action_help(self) -> None:
        """Show the help overlay modal listing every bound key (plan W5.5)."""
        self.push_screen(HelpScreen(lang=self._lang, bindings=SHELL_BINDINGS))

    def action_command_palette(self) -> None:
        """``:`` is reserved for a future command palette — v1 no-op."""
        return

    def action_expand_detail(self) -> None:
        """Open the Detail modal for the active tab if it's detail-capable."""
        tab_id = self._active_tab_id()
        if tab_id is None or not is_detail_capable(tab_id):
            return
        self.push_screen(
            DetailScreen(profile=self._profile, tab_id=tab_id, lang=self._lang)
        )

    def action_collapse_detail(self) -> None:
        """Esc from the shell — delegate to Textual's pop_screen if any modal
        is stacked on top. At the shell there's nothing to collapse."""
        return

    def _active_tab_id(self) -> str | None:
        try:
            tabs = self.query_one(TabbedContent)
        except Exception:
            return None
        active = tabs.active
        if not active or not active.startswith("pane-"):
            return None
        return active.removeprefix("pane-")


def run_tui(
    hermes_home: str | Path,
    *,
    name: str = "Hermes",
    lang: str = "en",
    theme_name: str = "hermes-teal",
    tab_width: int = 78,
    use_state_db: bool = True,
) -> int:
    """Blocking helper that boots the TUI. Returns the app's exit code."""
    theme = get_theme(theme_name)
    profile = load_profile(hermes_home, name=name, lang=lang, use_state_db=use_state_db)
    app = ShadowStatsApp(profile, lang=lang, theme=theme, tab_width=tab_width)
    app.run()
    return 0
