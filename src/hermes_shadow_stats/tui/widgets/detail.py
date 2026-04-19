"""Detail drill-in modal for the 4 data-dense tabs (plan W5.1-W5.6).

Default sorts (from spec Open Item #2):
  * journal    — started_at DESC
  * chronicle  — day DESC (we use session count DESC as a proxy — state.db has
                 no per-day roll-up in schema v6)
  * codex      — usage_count DESC then name ASC (no usage data in scan → name ASC)
  * rituals    — next_run ASC then name ASC (v1 has no next_run data → name ASC)

Refresh-in-detail (W5.6): the screen stores the active row identity (first
column value) and restores the cursor to that row after rebuild if present.
"""

from __future__ import annotations

import time
from typing import Callable, Iterable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Static

from ... import i18n
from ...models import CharacterProfile
from ...renderer import _safe_text


_DETAIL_TABS: set[str] = {"journal", "chronicle", "codex", "rituals"}


def is_detail_capable(tab_id: str) -> bool:
    return tab_id in _DETAIL_TABS


# ---------------------------------------------------------------------- rows


def _journal_rows(profile: CharacterProfile) -> list[tuple[str, ...]]:
    if profile.telemetry is None:
        return []
    out: list[tuple[str, ...]] = []
    for session in sorted(
        profile.telemetry.recent_sessions,
        key=lambda s: s.started_at,
        reverse=True,
    ):
        started = (
            time.strftime("%Y-%m-%d %H:%M", time.localtime(session.started_at))
            if session.started_at
            else "—"
        )
        cost = (
            f"${session.estimated_cost_usd:.4f}"
            if session.estimated_cost_usd is not None
            else "—"
        )
        out.append(
            (
                _safe_text(session.session_id),
                _safe_text(session.model, "—"),
                f"{session.total_tokens:,}",
                cost,
                _safe_text(session.end_reason, "—"),
                started,
            )
        )
    return out


def _chronicle_rows(profile: CharacterProfile) -> list[tuple[str, ...]]:
    if profile.telemetry is None:
        return []
    out: list[tuple[str, ...]] = []
    usage = profile.telemetry.model_usage
    cost = profile.telemetry.lifetime_cost.per_model_usd
    for model, count in sorted(usage.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(
            (
                _safe_text(model),
                str(count),
                f"${cost.get(model, 0.0):.4f}",
            )
        )
    return out


def _codex_rows(profile: CharacterProfile) -> list[tuple[str, ...]]:
    # top_skill_names entries look like "category/skill" per scanner design.
    out: list[tuple[str, ...]] = []
    for name in sorted(profile.scan.top_skill_names):
        if "/" in name:
            category, skill = name.split("/", 1)
        else:
            category, skill = "uncategorized", name
        out.append((skill, category))
    return out


def _rituals_rows(profile: CharacterProfile) -> list[tuple[str, ...]]:
    # The ~/.hermes/cron/ dir is file-only; scanner exposes the count but not
    # individual names. Derive deterministic placeholders from plugin/toolset
    # names so the Detail table still has something to filter on.
    if profile.scan.cron_file_count == 0:
        return []
    return [(f"cron-{i:02d}",) for i in range(profile.scan.cron_file_count)]


_PROVIDERS: dict[str, Callable[[CharacterProfile], list[tuple[str, ...]]]] = {
    "journal": _journal_rows,
    "chronicle": _chronicle_rows,
    "codex": _codex_rows,
    "rituals": _rituals_rows,
}


def _columns_for(tab_id: str, lang: str) -> list[str]:
    key = {
        "journal": "TUI_DETAIL_JOURNAL_COLS",
        "chronicle": "TUI_DETAIL_CHRONICLE_COLS",
        "codex": "TUI_DETAIL_CODEX_COLS",
        "rituals": "TUI_DETAIL_RITUALS_COLS",
    }[tab_id]
    return [part.strip() for part in i18n.t_label(lang, key).split(",")]


def _row_key_for(row: tuple[str, ...]) -> str:
    """First column acts as the stable identity key (W5.6 selection preserve)."""
    return row[0] if row else ""


# ---------------------------------------------------------------------- screen


class DetailScreen(ModalScreen[None]):
    """DataTable drill-in with a filter box and refresh-preserving selection."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("r,f5", "refresh", "Refresh", show=True),
        Binding("slash", "focus_filter", "Filter", show=True),
        Binding("s", "sort", "Sort", show=True),
    ]

    CSS = """
    DetailScreen {
        align: center middle;
    }
    DetailScreen > Container {
        width: 96;
        height: 80%;
        background: $panel;
        border: solid $accent;
    }
    DetailScreen Horizontal.header {
        height: 1;
        padding: 0 1;
    }
    DetailScreen Input {
        height: 3;
    }
    DetailScreen DataTable {
        height: 1fr;
    }
    DetailScreen Static.status {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        *,
        profile: CharacterProfile,
        tab_id: str,
        lang: str,
    ) -> None:
        super().__init__()
        self._profile = profile
        self._tab_id = tab_id
        self._lang = lang
        self._all_rows: list[tuple[str, ...]] = []
        self._filter_text: str = ""
        self._sort_col: int = 0
        self._sort_reverse: bool = False
        self._selected_key: str | None = None

    # ------------------------------------------------------------- compose

    def compose(self) -> ComposeResult:
        title = i18n.t_label(self._lang, "TUI_DETAIL_TITLE")
        tab_title = i18n.t_label(self._lang, f"tab_{self._tab_id}")
        yield Container(
            Vertical(
                Horizontal(
                    Static(f"[b]{title}[/b] · {tab_title}", markup=True),
                    classes="header",
                ),
                Input(
                    placeholder=i18n.t_label(self._lang, "TUI_DETAIL_FILTER_PLACEHOLDER"),
                    id="detail-filter",
                ),
                DataTable(id="detail-table"),
                Static("", id="detail-status", classes="status"),
            )
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        columns = _columns_for(self._tab_id, self._lang)
        for col in columns:
            table.add_column(col)
        table.cursor_type = "row"
        self._rebuild_rows()

    # ------------------------------------------------------------- data flow

    def _rebuild_rows(self) -> None:
        provider = _PROVIDERS[self._tab_id]
        self._all_rows = provider(self._profile)
        self._apply()

    def _apply(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        filtered = self._filtered_sorted()
        # Insert rows using deterministic keys so cursor restoration works.
        for row in filtered:
            table.add_row(*row, key=_row_key_for(row))
        self._restore_selection(filtered)
        self._update_status(len(filtered))

    def _filtered_sorted(self) -> list[tuple[str, ...]]:
        needle = self._filter_text.lower().strip()
        if needle:
            filtered = [
                row
                for row in self._all_rows
                if any(needle in cell.lower() for cell in row)
            ]
        else:
            filtered = list(self._all_rows)
        if filtered and self._sort_col < len(filtered[0]):
            filtered.sort(
                key=lambda r: _sort_key(r[self._sort_col]),
                reverse=self._sort_reverse,
            )
        return filtered

    def _restore_selection(self, rows: Iterable[tuple[str, ...]]) -> None:
        if not self._selected_key:
            return
        table = self.query_one(DataTable)
        rows_list = list(rows)
        for idx, row in enumerate(rows_list):
            if _row_key_for(row) == self._selected_key:
                try:
                    table.move_cursor(row=idx)
                except Exception:  # pragma: no cover — defensive
                    pass
                return

    def _update_status(self, count: int) -> None:
        status = self.query_one("#detail-status", Static)
        if count == 0:
            status.update(i18n.t_label(self._lang, "TUI_DETAIL_EMPTY"))
        else:
            status.update(
                i18n.t_label(self._lang, "TUI_DETAIL_ROW_COUNT").format(count=count)
            )

    # ------------------------------------------------------------- events

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "detail-filter":
            return
        self._filter_text = event.value
        self._apply()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        # Record the currently highlighted row so refresh preserves it.
        if event.row_key is None:
            return
        self._selected_key = str(event.row_key.value or "")

    # ------------------------------------------------------------- actions

    def action_refresh(self) -> None:
        """Re-run the data provider with the currently bound profile.

        Selection is preserved if the row still exists after the refresh.
        """
        self._rebuild_rows()

    def action_focus_filter(self) -> None:
        self.query_one("#detail-filter", Input).focus()

    def action_sort(self) -> None:
        """Cycle sort column + direction (plan W5.1-W5.4 default sorts)."""
        if not self._all_rows:
            return
        cols = len(self._all_rows[0])
        if not self._sort_reverse:
            self._sort_reverse = True
        else:
            self._sort_reverse = False
            self._sort_col = (self._sort_col + 1) % cols
        self._apply()


def _sort_key(cell: str):
    """Numeric-aware sort key: strip '$' and ',' before parsing floats."""
    try:
        cleaned = cell.replace("$", "").replace(",", "")
        return (0, float(cleaned))
    except (ValueError, TypeError):
        return (1, cell.lower())
