from __future__ import annotations

import json
from html import escape

from .models import CharacterProfile


STAT_LABELS = [
    ("STR", "strength"),
    ("INT", "intelligence"),
    ("WIS", "wisdom"),
    ("AGI", "agility"),
    ("CHA", "charisma"),
    ("LUK", "luck"),
]


PALETTE_BY_RANK = {
    "Bronze": {"accent": "#c08457", "accent_soft": "#f1c7a5"},
    "Silver": {"accent": "#c9d1d9", "accent_soft": "#edf2f7"},
    "Gold": {"accent": "#f5c451", "accent_soft": "#fde8a8"},
    "Mythic": {"accent": "#8b5cf6", "accent_soft": "#d8c4ff"},
}


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


def render_svg_card(profile: CharacterProfile) -> str:
    stats = profile.stats
    scan = profile.scan
    palette = PALETTE_BY_RANK.get(profile.rank, PALETTE_BY_RANK["Mythic"])
    accent = palette["accent"]
    accent_soft = palette["accent_soft"]
    background = "#09090f"
    panel = "#11131a"
    panel_soft = "#171b25"
    text = "#f5f7fb"
    text_dim = "#aab2c5"
    danger = "#ef4444"

    exp_width = int(420 * (stats.exp_into_level / max(stats.exp_to_next_level, 1)))
    domains = ", ".join(profile.dominant_domains[:3]) if profile.dominant_domains else "none"
    achievements = profile.achievements[:6]

    def stat_row(index: int, label: str, value: int) -> str:
        y = 222 + index * 36
        fill_width = int((value / 20) * 220)
        return f"""
        <text x="42" y="{y}" font-size="15" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(label)}</text>
        <rect x="105" y="{y - 14}" width="220" height="12" rx="6" fill="#242938"/>
        <rect x="105" y="{y - 14}" width="{fill_width}" height="12" rx="6" fill="{accent}"/>
        <text x="338" y="{y}" font-size="15" fill="{text}" font-family="Inter, Arial, sans-serif">{value}</text>
        """

    stat_rows = "".join(stat_row(i, label, getattr(stats, attr)) for i, (label, attr) in enumerate(STAT_LABELS))

    achievement_lines = []
    for i, achievement in enumerate(achievements):
        y = 508 + i * 24
        achievement_lines.append(
            f'<text x="420" y="{y}" font-size="14" fill="{text}" font-family="Inter, Arial, sans-serif">• {escape(achievement)}</text>'
        )
    if not achievement_lines:
        achievement_lines.append(
            f'<text x="420" y="508" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">• None yet</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="980" height="720" viewBox="0 0 980 720" role="img" aria-label="Hermes Shadow Stats card">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0b0c14"/>
      <stop offset="100%" stop-color="#141726"/>
    </linearGradient>
    <linearGradient id="accentGlow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{accent}"/>
      <stop offset="100%" stop-color="{accent_soft}"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>
  <rect width="980" height="720" fill="url(#bg)"/>
  <circle cx="840" cy="120" r="140" fill="{accent}" opacity="0.08"/>
  <circle cx="840" cy="120" r="90" fill="{accent}" opacity="0.08"/>

  <rect x="28" y="24" width="924" height="672" rx="26" fill="{background}" stroke="{accent}" stroke-width="2" filter="url(#shadow)"/>
  <rect x="28" y="24" width="924" height="80" rx="26" fill="{panel}"/>
  <text x="42" y="58" font-size="16" fill="{accent_soft}" font-family="Inter, Arial, sans-serif">HERMES SHADOW STATS</text>
  <text x="42" y="84" font-size="28" fill="{text}" font-family="Inter, Arial, sans-serif" font-weight="700">Status Window</text>
  <text x="700" y="58" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">Threat Evaluation</text>
  <text x="700" y="84" font-size="22" fill="{accent_soft}" font-family="Inter, Arial, sans-serif" font-weight="700">{escape(_field_signal(profile))}</text>

  <rect x="42" y="126" width="330" height="540" rx="20" fill="{panel}" stroke="#232838"/>
  <rect x="390" y="126" width="262" height="270" rx="20" fill="{panel}" stroke="#232838"/>
  <rect x="670" y="126" width="262" height="270" rx="20" fill="{panel}" stroke="#232838"/>
  <rect x="390" y="414" width="542" height="252" rx="20" fill="{panel}" stroke="#232838"/>

  <text x="42" y="160" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">ENTITY</text>
  <text x="42" y="198" font-size="34" fill="{text}" font-family="Inter, Arial, sans-serif" font-weight="700">{escape(profile.name)}</text>
  <text x="42" y="228" font-size="18" fill="{accent_soft}" font-family="Inter, Arial, sans-serif">{escape(profile.title)}</text>

  <text x="42" y="278" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">CLASS</text>
  <text x="42" y="304" font-size="22" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(profile.primary_class)}</text>
  <text x="200" y="278" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">RANK</text>
  <text x="200" y="304" font-size="22" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(profile.rank)}</text>

  <text x="42" y="352" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">LEVEL</text>
  <text x="42" y="384" font-size="42" fill="{accent_soft}" font-family="Inter, Arial, sans-serif" font-weight="700">{stats.level}</text>
  <text x="150" y="352" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">TOTAL EXP</text>
  <text x="150" y="384" font-size="24" fill="{text}" font-family="Inter, Arial, sans-serif">{stats.total_exp}</text>

  <text x="42" y="428" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">EXP GAUGE</text>
  <rect x="42" y="442" width="280" height="16" rx="8" fill="#242938"/>
  <rect x="42" y="442" width="{exp_width}" height="16" rx="8" fill="url(#accentGlow)"/>
  <text x="42" y="480" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{stats.exp_into_level}/{stats.exp_to_next_level} into next level</text>

  {stat_rows}

  <text x="410" y="160" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">GROWTH ECHOES</text>
  <text x="410" y="194" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Skills acquired: {scan.skill_count}</text>
  <text x="410" y="222" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Dominant domains: {escape(domains)}</text>
  <text x="410" y="250" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Memories absorbed: {scan.memory_entries}</text>
  <text x="410" y="278" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">User insight bonds: {scan.user_entries}</text>
  <text x="410" y="306" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Battle records: {scan.session_file_count}</text>
  <text x="410" y="334" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Automations bound: {scan.cron_file_count}</text>
  <text x="410" y="362" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Extensions equipped: {scan.plugin_count}</text>

  <text x="690" y="160" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">DEEP SIGNALS</text>
  <text x="690" y="194" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Tool-signatures: {scan.activity.session_tool_mentions}</text>
  <text x="690" y="222" font-size="16" fill="{danger if scan.activity.session_error_mentions else text}" font-family="Inter, Arial, sans-serif">Error scars: {scan.activity.session_error_mentions}</text>
  <text x="690" y="250" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Skill codex words: {scan.activity.skill_words}</text>
  <text x="690" y="278" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Plugin manifests: {scan.activity.plugin_manifest_count}</text>
  <text x="690" y="306" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Hook traces: {scan.activity.plugin_hook_mentions}</text>
  <text x="690" y="334" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Schedule glyphs: {scan.activity.cron_schedule_mentions}</text>
  <text x="690" y="362" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">Memory lines: {scan.activity.memory_lines}</text>

  <text x="410" y="448" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">ACHIEVEMENTS</text>
  {''.join(achievement_lines)}

  <text x="410" y="658" font-size="13" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(profile.summary[:92])}</text>
</svg>
"""


def render_json(profile: CharacterProfile) -> str:
    return json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)
