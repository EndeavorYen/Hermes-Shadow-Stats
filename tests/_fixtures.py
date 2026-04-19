"""Deterministic ``CharacterProfile`` fixtures for renderer tests.

These fixtures avoid file-scanner nondeterminism by constructing
``ScanSummary`` directly with hand-picked values that exercise a wide range
of renderer branches (skill categories, plugin slots, buffs, achievements,
CJK surname handling for zh-TW).
"""

from __future__ import annotations

from dataclasses import replace

from hermes_shadow_stats.models import (
    ActivitySignals,
    CostSummary,
    ScanSummary,
    SessionStats,
    TelemetrySnapshot,
    TokenUsage,
    ToolUsage,
)
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


# ---------------------------------------------------------------------------
# Phase 3 — telemetry fixtures (deterministic ``TelemetrySnapshot`` samples).
# ---------------------------------------------------------------------------

# Fixed epoch for deterministic timestamps (2026-04-17T12:00:00Z).
_BASE_TS: float = 1_776_614_400.0


def make_telemetry(
    *,
    session_count: int = 4,
    compression_events: int = 2,
    include_stale: bool = True,
    include_other_reason: bool = True,
) -> TelemetrySnapshot:
    """Return a deterministic ``TelemetrySnapshot`` covering the end_reason
    vocabulary plus an ``"other"``-bucketed value and a stale (``ended_at=None``)
    session so the diagnostics histogram exercises all rendering branches."""
    end_reasons = [
        "compression",
        "cron_complete",
        "user_exit",
        "branched",
    ]
    sessions: list[SessionStats] = []
    for idx in range(session_count):
        reason = end_reasons[idx % len(end_reasons)]
        ended_at = _BASE_TS - idx * 3600 + 600
        if include_stale and idx == 0:
            ended_at_val: float | None = None
        else:
            ended_at_val = ended_at
        sessions.append(
            SessionStats(
                session_id=f"sess-{idx:03d}",
                source="cli",
                model="opus-4-7" if idx % 2 == 0 else "sonnet-4-6",
                input_tokens=1200 + idx * 100,
                output_tokens=800 + idx * 50,
                cache_read_tokens=600 + idx * 40,
                cache_write_tokens=50 + idx * 5,
                reasoning_tokens=300 + idx * 20,
                message_count=40 + idx * 5,
                tool_call_count=12 + idx * 3,
                estimated_cost_usd=round(0.025 + idx * 0.005, 4),
                started_at=_BASE_TS - idx * 3600,
                ended_at=ended_at_val,
                end_reason=reason,
                parent_session_id=f"sess-{idx - 1:03d}" if idx > 0 else None,
                title=f"expedition {idx}",
            )
        )
    if include_other_reason and sessions:
        sessions[-1] = replace(sessions[-1], end_reason="unknown_reason")  # forces "other" bucket

    # Aggregate lifetime tokens / cost deterministically (mirrors hermes-agent
    # SUM() query results).
    total_input = sum(s.input_tokens for s in sessions)
    total_output = sum(s.output_tokens for s in sessions)
    total_cache_read = sum(s.cache_read_tokens for s in sessions)
    total_cache_write = sum(s.cache_write_tokens for s in sessions)
    total_reasoning = sum(s.reasoning_tokens for s in sessions)
    total_cost = round(sum((s.estimated_cost_usd or 0.0) for s in sessions), 4)
    per_model: dict[str, float] = {}
    for s in sessions:
        if s.model and s.estimated_cost_usd is not None:
            per_model[s.model] = round(per_model.get(s.model, 0.0) + s.estimated_cost_usd, 4)
    model_usage: dict[str, int] = {}
    for s in sessions:
        if s.model:
            model_usage[s.model] = model_usage.get(s.model, 0) + 1

    top_tools = [
        ToolUsage(tool_name="Read", invocation_count=120, last_used_at=_BASE_TS - 300),
        ToolUsage(tool_name="Edit", invocation_count=80, last_used_at=_BASE_TS - 600),
        ToolUsage(tool_name="Bash", invocation_count=45, last_used_at=_BASE_TS - 900),
        ToolUsage(tool_name="Grep", invocation_count=30, last_used_at=_BASE_TS - 1200),
        ToolUsage(tool_name="Glob", invocation_count=18, last_used_at=_BASE_TS - 1500),
    ]

    return TelemetrySnapshot(
        recent_sessions=sessions,
        lifetime_tokens=TokenUsage(
            input_tokens=total_input,
            output_tokens=total_output,
            cache_read_tokens=total_cache_read,
            cache_write_tokens=total_cache_write,
            reasoning_tokens=total_reasoning,
        ),
        lifetime_cost=CostSummary(total_usd=total_cost, per_model_usd=per_model),
        top_tools=top_tools,
        model_usage=model_usage,
        parent_chain_max_depth=session_count,
        compression_events=compression_events,
        session_count=session_count,
    )


def make_profile_with_telemetry(lang: str = "en"):
    """Deterministic profile including a fully populated ``TelemetrySnapshot``."""
    telemetry = make_telemetry()
    return build_character_profile(
        make_scan(),
        name="Hermes",
        lang=lang,
        telemetry=telemetry,
        fallback_reason=None,
    )


def make_fallback_profile(lang: str, fallback_reason: str):
    """Profile with no telemetry but explicit fallback_reason set."""
    return build_character_profile(
        make_scan(),
        name="Hermes",
        lang=lang,
        telemetry=None,
        fallback_reason=fallback_reason,
    )
