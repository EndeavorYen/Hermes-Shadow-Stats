"""Phase 5 Pilot tests: Detail drill-in, sort/filter, refresh selection, help overlay.

Per plan W5.7, these replace any manual QA gates. Screenshot diffs are
approximated by DataTable row-count and active-key assertions — sufficient
for CI without committing binary screenshot goldens.
"""

from __future__ import annotations

import asyncio

import pytest
from textual.widgets import DataTable, Input

from hermes_shadow_stats.renderer import TAB_IDS
from hermes_shadow_stats.tui import HERMES_TEAL, ShadowStatsApp
from hermes_shadow_stats.tui.widgets.detail import DetailScreen, is_detail_capable

from tests._fixtures import make_profile_with_telemetry


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------- capability

def test_detail_capable_tabs_registry() -> None:
    """Only the 4 data-dense tabs should open Detail."""
    expected = {"journal", "chronicle", "codex", "rituals"}
    assert {tid for tid in TAB_IDS if is_detail_capable(tid)} == expected


# ---------------------------------------------------------------- help overlay

def test_help_overlay_opens_on_question_mark() -> None:
    async def scenario() -> str:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_help()
            await pilot.pause()
            top = app.screen
            class_name = type(top).__name__
            app.pop_screen()
        return class_name

    assert _run(scenario()) == "HelpScreen"


# ---------------------------------------------------------------- detail open

@pytest.mark.parametrize("tab_id", ["journal", "chronicle", "codex", "rituals"])
def test_detail_opens_on_enter_for_data_dense_tabs(tab_id: str) -> None:
    async def scenario() -> tuple[str, int]:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Switch to the target tab before expanding detail.
            idx = TAB_IDS.index(tab_id)
            app.action_switch_tab(idx)
            await pilot.pause()
            app.action_expand_detail()
            await pilot.pause()
            top = app.screen
            table = top.query_one(DataTable)
            row_count = table.row_count
            cls = type(top).__name__
        return cls, row_count

    cls, _row_count = _run(scenario())
    assert cls == "DetailScreen"


def test_detail_does_not_open_for_summary_only_tabs() -> None:
    """Status/Equipment/Effects/Diagnostics have no Detail drill-in in v1."""

    async def scenario() -> list[str]:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        results: list[str] = []
        async with app.run_test() as pilot:
            await pilot.pause()
            for summary_only in ("status", "equipment", "effects", "diagnostics"):
                app.action_switch_tab(TAB_IDS.index(summary_only))
                await pilot.pause()
                app.action_expand_detail()
                await pilot.pause()
                results.append(type(app.screen).__name__)
        return results

    assert all(name != "DetailScreen" for name in _run(scenario()))


# ---------------------------------------------------------------- filter / sort

def test_journal_detail_filter_narrows_rows() -> None:
    async def scenario() -> tuple[int, int]:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_switch_tab(TAB_IDS.index("journal"))
            await pilot.pause()
            app.action_expand_detail()
            await pilot.pause()
            detail: DetailScreen = app.screen  # type: ignore[assignment]
            filter_input = detail.query_one("#detail-filter", Input)
            table = detail.query_one(DataTable)
            before = table.row_count
            # Fixture uses model "opus-4-7" on every even-indexed session.
            filter_input.value = "opus"
            await pilot.pause()
            after = table.row_count
        return before, after

    before, after = _run(scenario())
    assert before > 0
    assert 0 < after < before, f"filter did not narrow rows: {before=} {after=}"


def test_detail_sort_toggles_direction() -> None:
    async def scenario() -> list[bool]:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_switch_tab(TAB_IDS.index("journal"))
            await pilot.pause()
            app.action_expand_detail()
            await pilot.pause()
            detail: DetailScreen = app.screen  # type: ignore[assignment]
            state0 = detail._sort_reverse  # noqa: SLF001 — test inspects state
            detail.action_sort()
            state1 = detail._sort_reverse
            detail.action_sort()
            state2 = detail._sort_reverse
        return [state0, state1, state2]

    s = _run(scenario())
    assert s == [False, True, False]


# ---------------------------------------------------------------- refresh preserves selection

def test_refresh_preserves_row_selection() -> None:
    async def scenario() -> tuple[str, str]:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_switch_tab(TAB_IDS.index("journal"))
            await pilot.pause()
            app.action_expand_detail()
            await pilot.pause()
            detail: DetailScreen = app.screen  # type: ignore[assignment]
            table = detail.query_one(DataTable)
            # Move cursor to row 1 and capture its first-column value.
            table.move_cursor(row=1)
            await pilot.pause()
            # The RowHighlighted event fires asynchronously — simulate it by
            # reading the cell directly so the test is deterministic.
            selected_value = table.get_row_at(1)[0]
            detail._selected_key = selected_value  # noqa: SLF001 — direct set for test
            # Refresh — selection must survive.
            detail.action_refresh()
            await pilot.pause()
            table2 = detail.query_one(DataTable)
            cursor_after = table2.get_row_at(table2.cursor_row)[0]
        return selected_value, cursor_after

    before, after = _run(scenario())
    assert before == after, f"selection lost across refresh: before={before} after={after}"


# ---------------------------------------------------------------- escape closes

def test_escape_closes_detail() -> None:
    async def scenario() -> tuple[str, str]:
        profile = make_profile_with_telemetry(lang="en")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_switch_tab(TAB_IDS.index("codex"))
            await pilot.pause()
            app.action_expand_detail()
            await pilot.pause()
            on_detail = type(app.screen).__name__
            await pilot.press("escape")
            await pilot.pause()
            after = type(app.screen).__name__
        return on_detail, after

    on_detail, after = _run(scenario())
    assert on_detail == "DetailScreen"
    assert after != "DetailScreen"


# ---------------------------------------------------------------- empty state

def test_detail_shows_empty_state_when_no_rows() -> None:
    async def scenario() -> str:
        from tests._fixtures import make_fallback_profile

        profile = make_fallback_profile(lang="en", fallback_reason="no-state-db")
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_switch_tab(TAB_IDS.index("journal"))
            await pilot.pause()
            app.action_expand_detail()
            await pilot.pause()
            detail = app.screen
            from textual.widgets import Static

            status = detail.query_one("#detail-status", Static)
            # Textual's Static.renderable could be str or Text; extract text.
            return str(status.renderable)

    msg = _run(scenario())
    from hermes_shadow_stats import i18n

    assert i18n.t_label("en", "TUI_DETAIL_EMPTY") in msg
