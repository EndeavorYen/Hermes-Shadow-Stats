from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ActivitySignals:
    memory_lines: int
    skill_words: int
    session_tool_mentions: int
    session_error_mentions: int
    plugin_manifest_count: int
    plugin_hook_mentions: int
    cron_schedule_mentions: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScanSummary:
    hermes_home: str
    memory_entries: int
    user_entries: int
    skill_count: int
    skill_categories: dict[str, int]
    profile_count: int
    session_file_count: int
    plugin_count: int
    log_file_count: int
    cron_file_count: int
    activity: ActivitySignals
    plugin_names: list[str] = field(default_factory=list)
    recent_sessions: list[str] = field(default_factory=list)
    top_skill_names: list[str] = field(default_factory=list)
    toolset_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StatBlock:
    level: int
    exp_into_level: int
    exp_to_next_level: int
    total_exp: int
    strength: int
    intelligence: int
    wisdom: int
    agility: int
    charisma: int
    luck: int
    # Phase 2 additions (ref: plan W2.5). None == telemetry unavailable.
    endurance: int | None = None
    precision: int | None = None
    resonance: int | None = None
    clarity: int | None = None
    reach: int | None = None
    tempo: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Phase 2: state.db telemetry dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SessionStats:
    """Single-session metadata read from ``sessions`` table (read-only)."""

    session_id: str
    source: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    message_count: int = 0
    tool_call_count: int = 0
    estimated_cost_usd: float | None = None
    started_at: float = 0.0
    ended_at: float | None = None
    end_reason: str | None = None
    parent_session_id: str | None = None
    title: str | None = None

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
            + self.reasoning_tokens
        )

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return max(0.0, self.ended_at - self.started_at)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0

    @property
    def total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
            + self.reasoning_tokens
        )

    @property
    def cache_hit_rate(self) -> float:
        """Fraction of read tokens that came from cache.

        Denominator is ``cache_read_tokens + input_tokens`` — "how much of the
        prompt side was served from cache". Returns 0.0 when no prompt tokens.
        """
        denom = self.cache_read_tokens + self.input_tokens
        return (self.cache_read_tokens / denom) if denom else 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CostSummary:
    total_usd: float = 0.0
    per_model_usd: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ToolUsage:
    tool_name: str
    invocation_count: int
    last_used_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TelemetrySnapshot:
    """Aggregated snapshot from ``~/.hermes/state.db`` (read-only, schema v6).

    Every field degrades gracefully to its zero-value when the DB query fails
    or yields no rows, so callers can render partial data.
    """

    recent_sessions: list[SessionStats] = field(default_factory=list)
    lifetime_tokens: TokenUsage = field(default_factory=TokenUsage)
    lifetime_cost: CostSummary = field(default_factory=CostSummary)
    top_tools: list[ToolUsage] = field(default_factory=list)
    model_usage: dict[str, int] = field(default_factory=dict)
    parent_chain_max_depth: int = 0
    compression_events: int = 0  # end_reason == 'compression' (run_agent.py:7177)
    session_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Equipment:
    """RPG equipment mapping (Phase 2 W2.6): replaces old plugin_names[:3] hack.

    - ``main_weapon``: current model (from most-recent session)
    - ``armor_slots``: plugin names (multi-slot)
    - ``trinkets``: enabled toolset names
    - ``hotbar``: top 5 most-used tools from state.db messages
    """

    main_weapon: str | None = None
    armor_slots: list[str] = field(default_factory=list)
    trinkets: list[str] = field(default_factory=list)
    hotbar: list[ToolUsage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ThemePreset:
    """ANSI/TUI theme preset (Phase 4 W4.4)."""

    name: str
    background: str
    foreground: str
    accent: str
    success: str
    warning: str
    danger: str
    muted: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TabSpec:
    """Per-tab metadata consumed by the TUI shell (Phase 4)."""

    id: str
    title_key: str  # i18n key, e.g. "tab_status"
    is_data_dense: bool  # True ⇒ Detail drill-in available (Phase 5)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# CharacterProfile (extended with optional telemetry/equipment fields)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class CharacterProfile:
    name: str
    title: str
    primary_class: str
    rank: str
    summary: str
    stats: StatBlock
    scan: ScanSummary
    achievements: list[str] = field(default_factory=list)
    dominant_domains: list[str] = field(default_factory=list)
    lang: str = "en"
    primary_class_id: str = ""
    rank_id: str = ""
    achievement_ids: list[str] = field(default_factory=list)
    buff_ids: list[str] = field(default_factory=list)
    threat_id: str = ""
    awakening_id: str = ""
    # Phase 2 optional telemetry fields — None when state.db unavailable.
    telemetry: TelemetrySnapshot | None = None
    equipment: Equipment | None = None
    # Reason why telemetry is absent; drives the fallback banner in Status tab.
    # Values: "no-state-db" | "schema-fallback" | "state-db-unreadable" | None
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
