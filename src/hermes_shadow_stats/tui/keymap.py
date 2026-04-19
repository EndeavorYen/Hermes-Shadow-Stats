"""Declarative Bindings for the Shadow Stats TUI (plan W4.3).

Kept isolated from ``app.py`` so Phase 5 Detail views can import the same list
and extend it without circular imports.
"""

from __future__ import annotations

from textual.binding import Binding


# Per spec keymap: ←/→/h/l/1-8/Enter/Esc/r/F5/q/?/:
SHELL_BINDINGS: list[Binding] = [
    # Tab navigation (cyclic).
    Binding("right,l", "next_tab", "Next tab", show=False),
    Binding("left,h", "previous_tab", "Prev tab", show=False),
    # Direct tab selection (digits 1..8 map onto TAB_IDS indices).
    Binding("1", "switch_tab(0)", "Status", show=False),
    Binding("2", "switch_tab(1)", "Equipment", show=False),
    Binding("3", "switch_tab(2)", "Codex", show=False),
    Binding("4", "switch_tab(3)", "Journal", show=False),
    Binding("5", "switch_tab(4)", "Chronicle", show=False),
    Binding("6", "switch_tab(5)", "Rituals", show=False),
    Binding("7", "switch_tab(6)", "Effects", show=False),
    Binding("8", "switch_tab(7)", "Diagnostics", show=False),
    # Detail drill-in (wired in Phase 5 on detail-capable tabs).
    Binding("enter", "expand_detail", "Detail", show=False),
    Binding("escape", "collapse_detail", "Back", show=False),
    # Global actions.
    Binding("r,f5", "refresh_snapshot", "Refresh", show=True),
    Binding("question_mark", "help", "Help", show=True),
    Binding("colon", "command_palette", "Command", show=False),
    Binding("q,ctrl+c", "quit", "Quit", show=True),
]
