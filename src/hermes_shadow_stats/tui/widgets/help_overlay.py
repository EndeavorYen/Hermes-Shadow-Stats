"""Help overlay modal (plan W5.5).

Displays every shell binding that has a human-readable description. i18n
keys come from the ``TUI_*`` namespace (Phase 6 completeness test asserts
both ``en`` and ``zh-TW`` coverage).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static

from ... import i18n


class HelpScreen(ModalScreen[None]):
    """Dismiss-on-any-key modal listing all current key bindings."""

    BINDINGS = [
        Binding("escape,q,question_mark,enter", "app.pop_screen", "Close", show=False),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Container {
        width: 64;
        height: auto;
        background: $panel;
        border: solid $accent;
        padding: 1 2;
    }
    HelpScreen Static {
        width: auto;
    }
    """

    def __init__(self, lang: str, bindings: list[Binding]) -> None:
        super().__init__()
        self._lang = lang
        self._bindings = bindings

    def compose(self) -> ComposeResult:
        title = i18n.t_label(self._lang, "TUI_HELP_TITLE")
        close_hint = i18n.t_label(self._lang, "TUI_HELP_CLOSE")
        lines: list[str] = [f"[b]{title}[/b]", ""]
        for binding in self._bindings:
            if not binding.description:
                continue
            lines.append(f"  [b]{binding.key}[/b]  · {binding.description}")
        lines.append("")
        lines.append(f"[dim]{close_hint}[/dim]")
        yield Container(Static("\n".join(lines), markup=True))
