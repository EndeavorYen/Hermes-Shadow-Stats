from __future__ import annotations

import json

from .models import CharacterProfile


STAT_LABELS = [
    ("STR", "strength"),
    ("INT", "intelligence"),
    ("WIS", "wisdom"),
    ("AGI", "agility"),
    ("CHA", "charisma"),
    ("LUK", "luck"),
]


def _bar(value: int, max_value: int = 20, width: int = 10, filled: str = "■", empty: str = "□") -> str:
    filled_count = round((value / max_value) * width)
    return filled * filled_count + empty * (width - filled_count)


def _rank_emblem(rank: str) -> str:
    return {
        "Bronze": "🟫",
        "Silver": "⬜",
        "Gold": "🟨",
        "Mythic": "🟪",
    }.get(rank, "◼")


def _field_signal(profile: CharacterProfile) -> str:
    score = (
        len(profile.dominant_domains)
        + min(profile.scan.plugin_count, 3)
        + min(profile.scan.cron_file_count, 3)
        + min(profile.scan.session_file_count // 25, 4)
        + min(profile.scan.activity.session_tool_mentions // 40, 3)
    )
    if score >= 10:
        return "Monarch-class anomaly"
    if score >= 7:
        return "S-rank awakening"
    if score >= 4:
        return "High-tier hunter"
    return "Rookie presence"


def render_markdown(profile: CharacterProfile) -> str:
    stats = profile.stats
    scan = profile.scan
    exp_bar = _bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=16, filled="█", empty="░")

    lines = [
        "# Hermes Shadow Stats",
        "",
        "> The system has acknowledged this entity.",
        "",
        f"## {_rank_emblem(profile.rank)} Status Window",
        f"- **Name**: {profile.name}",
        f"- **Title**: {profile.title}",
        f"- **Class**: {profile.primary_class}",
        f"- **Rank**: {profile.rank}",
        f"- **Threat Evaluation**: {_field_signal(profile)}",
        f"- **Level**: {stats.level}",
        f"- **EXP Gauge**: `{exp_bar}` {stats.exp_into_level}/{stats.exp_to_next_level} _(total: {stats.total_exp})_",
        "",
        "## Base Attributes",
    ]

    for label, attr in STAT_LABELS:
        value = getattr(stats, attr)
        lines.append(f"- **{label}** {value:>2}  `{_bar(value)}`")

    lines.extend([
        "",
        "## Growth Echoes",
        f"- **Memories absorbed**: {scan.memory_entries}",
        f"- **User insight bonds**: {scan.user_entries}",
        f"- **Skills acquired**: {scan.skill_count}",
        f"- **Dominant domains**: {', '.join(profile.dominant_domains) if profile.dominant_domains else 'none'}",
        f"- **Alternate profiles**: {scan.profile_count}",
        f"- **Battle records**: {scan.session_file_count}",
        f"- **Extensions equipped**: {scan.plugin_count}",
        f"- **Log echoes**: {scan.log_file_count}",
        f"- **Automations bound**: {scan.cron_file_count}",
        "",
        "## Deep Signals",
        f"- **Memory lines parsed**: {scan.activity.memory_lines}",
        f"- **Skill codex words**: {scan.activity.skill_words}",
        f"- **Tool-signatures in sessions**: {scan.activity.session_tool_mentions}",
        f"- **Error scars observed**: {scan.activity.session_error_mentions}",
        f"- **Plugin manifests**: {scan.activity.plugin_manifest_count}",
        f"- **Hook traces**: {scan.activity.plugin_hook_mentions}",
        f"- **Schedule glyphs**: {scan.activity.cron_schedule_mentions}",
        "",
        "## Titles & Achievements",
    ])

    if profile.achievements:
        lines.extend(f"- {achievement}" for achievement in profile.achievements)
    else:
        lines.append("- No public achievements yet")

    lines.extend([
        "",
        "## Narrative Summary",
        profile.summary,
    ])

    return "\n".join(lines)


def render_ascii_panel(profile: CharacterProfile) -> str:
    stats = profile.stats
    scan = profile.scan
    width = 66
    top = "+" + "=" * width + "+"
    divider = "+" + "-" * width + "+"

    def row(text: str = "") -> str:
        trimmed = text[:width]
        return f"| {trimmed:<{width-1}}|"

    lines = [
        top,
        row("HERMES SHADOW STATS // STATUS WINDOW"),
        divider,
        row(f"Name  : {profile.name}"),
        row(f"Title : {profile.title}"),
        row(f"Class : {profile.primary_class}"),
        row(f"Rank  : {profile.rank}"),
        row(f"Level : {stats.level}    Threat: {_field_signal(profile)}"),
        row(f"EXP   : {_bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=20, filled='#', empty='-')} {stats.exp_into_level}/{stats.exp_to_next_level}"),
        divider,
        row("ATTRIBUTES"),
    ]

    for label, attr in STAT_LABELS:
        value = getattr(stats, attr)
        lines.append(row(f"{label:<4}: {value:>2}  {_bar(value, width=16, filled='#', empty='-')}"))

    lines.extend([
        divider,
        row("GROWTH ECHOES"),
        row(f"skills={scan.skill_count}  domains={', '.join(profile.dominant_domains) if profile.dominant_domains else 'none'}"),
        row(f"memories={scan.memory_entries}  user={scan.user_entries}  sessions={scan.session_file_count}"),
        row(f"plugins={scan.plugin_count}  cron={scan.cron_file_count}  logs={scan.log_file_count}"),
        row(f"tool-signatures={scan.activity.session_tool_mentions}  hook-traces={scan.activity.plugin_hook_mentions}"),
        divider,
        row("ACHIEVEMENTS"),
    ])

    if profile.achievements:
        for achievement in profile.achievements[:8]:
            lines.append(row(f"- {achievement}"))
    else:
        lines.append(row("- None yet"))

    lines.extend([
        divider,
        row(profile.summary),
        top,
    ])
    return "\n".join(lines)


def render_json(profile: CharacterProfile) -> str:
    return json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)
