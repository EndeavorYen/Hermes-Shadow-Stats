"""Deterministic ``CharacterProfile`` fixtures for renderer tests.

These fixtures avoid file-scanner nondeterminism by constructing
``ScanSummary`` directly with hand-picked values that exercise a wide range
of renderer branches (skill categories, plugin slots, buffs, achievements,
CJK surname handling for zh-TW).
"""

from __future__ import annotations

from hermes_shadow_stats.models import ActivitySignals, ScanSummary
from hermes_shadow_stats.stats import build_character_profile


def make_scan(
    *,
    hermes_home: str = "/home/test/.hermes",
    memory_entries: int = 5,
    user_entries: int = 3,
    skill_count: int = 15,
    skill_categories: dict[str, int] | None = None,
    profile_count: int = 2,
    session_file_count: int = 50,
    plugin_count: int = 3,
    log_file_count: int = 12,
    cron_file_count: int = 2,
    plugin_names: list[str] | None = None,
    recent_sessions: list[str] | None = None,
    top_skill_names: list[str] | None = None,
    activity: ActivitySignals | None = None,
) -> ScanSummary:
    return ScanSummary(
        hermes_home=hermes_home,
        memory_entries=memory_entries,
        user_entries=user_entries,
        skill_count=skill_count,
        skill_categories=skill_categories
        or {"github": 4, "research": 3, "writing": 2, "misc": 6},
        profile_count=profile_count,
        session_file_count=session_file_count,
        plugin_count=plugin_count,
        log_file_count=log_file_count,
        cron_file_count=cron_file_count,
        activity=activity
        or ActivitySignals(
            memory_lines=40,
            skill_words=2000,
            session_tool_mentions=85,
            session_error_mentions=4,
            plugin_manifest_count=2,
            plugin_hook_mentions=6,
            cron_schedule_mentions=5,
        ),
        plugin_names=plugin_names
        or ["shadow", "greptile", "context7"],
        recent_sessions=recent_sessions
        or [
            "2026-04-17",
            "2026-04-16",
            "2026-04-15",
            "2026-04-14",
            "2026-04-13",
        ],
        top_skill_names=top_skill_names
        or [
            "github/repo-management",
            "research/blogwatcher",
            "writing/docs",
            "misc/note",
            "misc/todo",
        ],
    )


def make_profile(lang: str = "en", **scan_overrides):
    """Build a deterministic ``CharacterProfile`` for rendering tests."""
    return build_character_profile(make_scan(**scan_overrides), name="Hermes", lang=lang)
