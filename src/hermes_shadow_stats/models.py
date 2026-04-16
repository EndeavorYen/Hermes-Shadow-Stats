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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
