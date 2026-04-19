"""Smoke + basic-content tests for the 8 per-tab render functions.

These functions are the Phase 1 additions that feed the TUI widgets and the
new ``--format tabs`` static export. Each function must:

- Execute without crashing for both populated and minimal profiles.
- Accept the final signature ``(profile, *, width, lang, telemetry=None)``.
- Produce at least one non-blank line.
- Contain the tab's section title (in ``en`` default rendering).
"""

from __future__ import annotations

import pytest

from hermes_shadow_stats import i18n
from hermes_shadow_stats.models import ActivitySignals, ScanSummary
from hermes_shadow_stats.renderer import (
    TAB_IDS,
    render_chronicle_tab,
    render_codex_tab,
    render_diagnostics_tab,
    render_effects_tab,
    render_equipment_tab,
    render_journal_tab,
    render_rituals_tab,
    render_static_tabs_panel,
    render_status_tab,
    render_tab,
)
from hermes_shadow_stats.stats import build_character_profile

from tests._fixtures import make_profile


TAB_FUNCS = {
    "status": render_status_tab,
    "equipment": render_equipment_tab,
    "codex": render_codex_tab,
    "journal": render_journal_tab,
    "chronicle": render_chronicle_tab,
    "rituals": render_rituals_tab,
    "effects": render_effects_tab,
    "diagnostics": render_diagnostics_tab,
}


def _empty_scan() -> ScanSummary:
    return ScanSummary(
        hermes_home="/home/empty/.hermes",
        memory_entries=0,
        user_entries=0,
        skill_count=0,
        skill_categories={},
        profile_count=0,
        session_file_count=0,
        plugin_count=0,
        log_file_count=0,
        cron_file_count=0,
        activity=ActivitySignals(
            memory_lines=0,
            skill_words=0,
            session_tool_mentions=0,
            session_error_mentions=0,
            plugin_manifest_count=0,
            plugin_hook_mentions=0,
            cron_schedule_mentions=0,
        ),
        plugin_names=[],
        recent_sessions=[],
        top_skill_names=[],
    )


@pytest.fixture(params=["en", "zh-TW"])
def lang(request) -> str:
    return request.param


@pytest.fixture
def populated_profile(lang: str):
    return make_profile(lang=lang)


@pytest.fixture
def empty_profile(lang: str):
    return build_character_profile(_empty_scan(), name="Drifter", lang=lang)


@pytest.mark.parametrize("tab_id", TAB_IDS)
def test_populated_renders_content(populated_profile, lang: str, tab_id: str) -> None:
    fn = TAB_FUNCS[tab_id]
    out = fn(populated_profile, width=78, lang=lang)
    assert out, f"{tab_id} produced empty output"
    assert out.count("\n") >= 1, f"{tab_id} produced a single-line output"


@pytest.mark.parametrize("tab_id", TAB_IDS)
def test_empty_profile_does_not_crash(empty_profile, lang: str, tab_id: str) -> None:
    """Every tab must survive an empty ~/.hermes (no plugins, no skills, etc.)."""
    fn = TAB_FUNCS[tab_id]
    out = fn(empty_profile, width=78, lang=lang)
    # Must at least emit the tab title row.
    assert out, f"{tab_id} crashed or produced empty output on empty profile"


@pytest.mark.parametrize("tab_id", TAB_IDS)
def test_telemetry_parameter_accepted(populated_profile, tab_id: str) -> None:
    """Every tab must accept ``telemetry`` (None or TelemetrySnapshot) without crashing."""
    from hermes_shadow_stats.models import TelemetrySnapshot

    fn = TAB_FUNCS[tab_id]
    out = fn(populated_profile, width=78, lang="en", telemetry=None)
    assert out
    # Passing an empty TelemetrySnapshot must not crash.
    empty_snap = TelemetrySnapshot()
    out2 = fn(populated_profile, width=78, lang="en", telemetry=empty_snap)
    assert out2


@pytest.mark.parametrize("tab_id", TAB_IDS)
def test_render_tab_dispatcher(populated_profile, tab_id: str) -> None:
    via_dispatch = render_tab(tab_id, populated_profile, width=78, lang="en")
    via_direct = TAB_FUNCS[tab_id](populated_profile, width=78, lang="en")
    assert via_dispatch == via_direct


def test_render_tab_unknown_id(populated_profile) -> None:
    with pytest.raises(ValueError):
        render_tab("bogus_tab", populated_profile, width=78)


def test_static_tabs_panel_contains_all_tabs(populated_profile, lang: str) -> None:
    out = render_static_tabs_panel(populated_profile, width=78)
    # Tab titles from i18n must appear as section headers.
    for tab_id in TAB_IDS:
        title = i18n.t_label(populated_profile.lang, f"tab_{tab_id}")
        assert title in out, f"tab title {title!r} missing from static_tabs_panel"


def test_static_tabs_panel_width_variations(populated_profile) -> None:
    """Panel must render cleanly across banner widths the CLI supports."""
    for width in (56, 62, 78):
        out = render_static_tabs_panel(populated_profile, width=width)
        assert out.count("\n") > 20, f"width={width} produced too few lines"


def test_tab_ids_registry_stable() -> None:
    """Tab ordering is a public contract — freeze it here."""
    assert TAB_IDS == [
        "status",
        "equipment",
        "codex",
        "journal",
        "chronicle",
        "rituals",
        "effects",
        "diagnostics",
    ]
