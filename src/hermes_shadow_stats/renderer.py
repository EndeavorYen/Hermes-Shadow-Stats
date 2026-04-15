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

CLI_LOGO_ROWS_WIDE = [
    "██   ██ ███████ ██████  ███    ███ ███████ ███████",
    "██   ██ ██      ██   ██ ████  ████ ██      ██     ",
    "███████ █████   ██████  ██ ████ ██ █████   ███████",
    "██   ██ ██      ██   ██ ██  ██  ██ ██           ██",
    "██   ██ ███████ ██   ██ ██      ██ ███████ ███████",
]

CLI_LOGO_ROWS_COMPACT = [
    "██ ██ ████ ████ ████ ████",
    "████ ███  ████ ████ █████",
    "██ ██ ████ ████ ████ ████",
]


PALETTE_BY_RANK = {
    "Bronze": {"accent": "#c08457", "accent_soft": "#f1c7a5"},
    "Silver": {"accent": "#c9d1d9", "accent_soft": "#edf2f7"},
    "Gold": {"accent": "#f5c451", "accent_soft": "#fde8a8"},
    "Mythic": {"accent": "#8b5cf6", "accent_soft": "#d8c4ff"},
}


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "black": "\033[30m",
    "white": "\033[97m",
    "soft": "\033[38;5;153m",
    "lavender": "\033[38;5;117m",
    "violet": "\033[38;5;111m",
    "deep_violet": "\033[38;5;69m",
    "gold": "\033[38;5;221m",
    "silver": "\033[38;5;250m",
    "bronze": "\033[38;5;110m",
    "cyan": "\033[38;5;153m",
    "ice": "\033[38;5;117m",
    "blue": "\033[38;5;111m",
    "indigo": "\033[38;5;69m",
    "red": "\033[38;5;203m",
    "gray": "\033[38;5;245m",
    "slate": "\033[38;5;103m",
    "bg": "\033[48;5;233m",
    "bg_soft": "\033[48;5;235m",
    "bg_panel": "\033[48;5;234m",
}


def _bar(value: int, max_value: int = 20, width: int = 10, filled: str = "■", empty: str = "□") -> str:
    filled_count = round((value / max_value) * width)
    return filled * filled_count + empty * (width - filled_count)


def _rank_emblem(rank: str) -> str:
    return {
        "Bronze": "+",
        "Silver": "*",
        "Gold": "#",
        "Mythic": "@",
    }.get(rank, "+")


def _rank_color(rank: str) -> str:
    return {
        "Bronze": ANSI["bronze"],
        "Silver": ANSI["silver"],
        "Gold": ANSI["gold"],
        "Mythic": ANSI["lavender"],
    }.get(rank, ANSI["violet"])


def _field_signal(profile: CharacterProfile) -> str:
    score = (
        len(profile.dominant_domains)
        + min(profile.scan.plugin_count, 3)
        + min(profile.scan.cron_file_count, 3)
        + min(profile.scan.session_file_count // 25, 4)
        + min(profile.scan.activity.session_tool_mentions // 40, 3)
    )
    if score >= 10:
        return "Archive anomaly"
    if score >= 7:
        return "System ascendant"
    if score >= 4:
        return "Field-ready hunter"
    return "Candidate presence"


def _awakening_stage(profile: CharacterProfile) -> str:
    level = profile.stats.level
    if level >= 40:
        return "System Overclock"
    if level >= 25:
        return "Shadow Awakening"
    if level >= 14:
        return "Hunter Ascension"
    if level >= 7:
        return "Class Emergence"
    return "Candidate Phase"


def _class_emblem(primary_class: str) -> str:
    return {
        "Toolsmith": "#",
        "Code Alchemist": "*",
        "Ops Summoner": "~",
        "Research Ranger": ">",
        "Memory Weaver": "&",
        "Workflow Scribe": "=",
        "Model Hunter": "@",
        "Shadow Commander": "!",
        "Rune Artisan": "%",
        "Signal Duelist": "^",
        "Protocol Walker": "$",
        "Adaptive Agent": "+",
        "Hunter Candidate": "-",
    }.get(primary_class, "+")


def _ansi(text: str, *codes: str) -> str:
    return "".join(codes) + text + ANSI["reset"]


def _visible_len(text: str) -> int:
    import re
    return len(re.sub(r"\x1b\[[0-9;]*m", "", text))


def _truncate_ansi(text: str, width: int) -> str:
    import re

    result: list[str] = []
    visible = 0
    for token in re.findall(r"\x1b\[[0-9;]*m|.", text):
        if token.startswith("\x1b"):
            result.append(token)
            continue
        if visible >= width:
            break
        result.append(token)
        visible += 1
    if result and not result[-1].endswith(ANSI["reset"]):
        result.append(ANSI["reset"])
    return "".join(result)


def _ansi_row(text: str, width: int = 76, border_color: str | None = None) -> str:
    border = _ansi("│", border_color or ANSI["deep_violet"], ANSI["dim"])
    if _visible_len(text) > width:
        text = _truncate_ansi(text, width)
    visible = _visible_len(text)
    return f"{border} {text}{' ' * max(0, width - visible)} {border}"


def _ansi_section(title: str, width: int = 76, color: str | None = None) -> str:
    color = color or ANSI["lavender"]
    title = f" {title} "
    line = "═" * max(4, width - len(title) - 2)
    return _ansi(f"╞{title}{line}╡", ANSI["bold"], color)


def _wrap_plain(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= width:
            current += f" {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_ansi(text: str, width: int) -> str:
    if _visible_len(text) > width:
        text = _truncate_ansi(text, width)
    return f"{text}{' ' * max(0, width - _visible_len(text))}"


def _center_ansi(text: str, width: int) -> str:
    if _visible_len(text) > width:
        text = _truncate_ansi(text, width)
    visible = _visible_len(text)
    left_pad = max(0, (width - visible) // 2)
    right_pad = max(0, width - visible - left_pad)
    return f"{' ' * left_pad}{text}{' ' * right_pad}"


def _pair(left: str, right: str, width: int, gap: int = 2) -> str:
    left_width = (width - gap) // 2
    right_width = width - gap - left_width
    return f"{_fit_ansi(left, left_width)}{' ' * gap}{_fit_ansi(right, right_width)}"


def _resolve_banner_mode(width: int, banner_mode: str = "auto") -> str:
    if banner_mode != "auto":
        return banner_mode
    if width >= 76:
        return "wide"
    if width >= 62:
        return "compact"
    return "minimal"


def _cli_logo_banner(width: int, frame_color: str, banner_mode: str = "auto") -> list[str]:
    mode = _resolve_banner_mode(width, banner_mode)
    if mode == "minimal":
        return [
            _ansi_row(_center_ansi(_ansi("HERMES // SHADOW PROFILE", ANSI["bold"], ANSI["white"]), width), width, frame_color),
            _ansi_row(_center_ansi(_ansi("status window // ansi mode", ANSI["bold"], ANSI["cyan"]), width), width, frame_color),
        ]

    logo_rows = CLI_LOGO_ROWS_WIDE if mode == "wide" else CLI_LOGO_ROWS_COMPACT
    shadow_rows = [f"  {row}" for row in logo_rows]
    palette = [ANSI["white"], ANSI["soft"], ANSI["ice"], ANSI["blue"], ANSI["deep_violet"]]
    colors = [palette[min(i, len(palette) - 1)] for i in range(len(logo_rows))]
    lines: list[str] = []
    for shadow, row, color in zip(shadow_rows, logo_rows, colors, strict=False):
        lines.append(_ansi_row(_center_ansi(_ansi(shadow.rstrip(), ANSI["dim"], ANSI["indigo"]), width), width, frame_color))
        lines.append(_ansi_row(_center_ansi(_ansi(row.rstrip(), ANSI["bold"], color), width), width, frame_color))
    subtitle = "HERMES SHADOW PROFILE // STATUS WINDOW" if mode == "wide" else "HERMES // SHADOW PROFILE // ANSI WINDOW"
    lines.append(_ansi_row(_center_ansi(_ansi(subtitle, ANSI["bold"], ANSI["cyan"]), width), width, frame_color))
    return lines


def _stacked_value_rows(
    label: str,
    value: str,
    width: int,
    frame_color: str,
    *,
    label_color: str | None = None,
    value_color: str | None = None,
    indent: int = 2,
) -> list[str]:
    label_text = _ansi(label, ANSI["dim"], label_color or ANSI["soft"])
    value_lines = _wrap_plain(value, max(8, width - len(label) - indent))
    rows = [_ansi_row(f"{label_text}{' ' * indent}{_ansi(value_lines[0], value_color or ANSI['white'])}", width, frame_color)]
    continuation = " " * (len(label) + indent)
    for extra_line in value_lines[1:]:
        rows.append(_ansi_row(f"{continuation}{_ansi(extra_line, value_color or ANSI['white'])}", width, frame_color))
    return rows


def _top_summary_rows(
    profile: CharacterProfile,
    width: int,
    frame_color: str,
    threat: str,
    awakening: str,
    emblem: str,
    mode: str,
) -> list[str]:
    if mode == "wide":
        return [
            _ansi_row(_pair(
                _ansi(f"[ STATUS ] {profile.rank} rank // lvl {profile.stats.level}", ANSI["bold"], ANSI["cyan"]),
                _ansi(f"[ THREAT CLASS ] {threat}", ANSI["bold"], ANSI["gold"]),
                width,
            ), width, frame_color),
            _ansi_row(_pair(
                _ansi(f"[ AWAKENING ] {awakening}", ANSI["bold"], ANSI["lavender"]),
                _ansi(f"[ CLASS SIGIL ] {profile.primary_class} {emblem}", ANSI["bold"], ANSI["ice"]),
                width,
            ), width, frame_color),
        ]

    if mode == "compact":
        return [
            _ansi_row(_ansi(f"[ STATUS ] {profile.rank} // Lv {profile.stats.level}", ANSI["bold"], ANSI["cyan"]), width, frame_color),
            _ansi_row(_ansi(f"[ THREAT ] {threat}", ANSI["bold"], ANSI["gold"]), width, frame_color),
            _ansi_row(_ansi(f"[ AWAKENING ] {awakening}", ANSI["bold"], ANSI["lavender"]), width, frame_color),
            _ansi_row(_ansi(f"[ CLASS SIGIL ] {profile.primary_class} {emblem}", ANSI["bold"], ANSI["ice"]), width, frame_color),
        ]

    return [
        _ansi_row(_ansi(f"[ STATUS ] {profile.rank} // Lv {profile.stats.level}", ANSI["bold"], ANSI["cyan"]), width, frame_color),
        _ansi_row(_ansi(f"[ THREAT ] {threat}", ANSI["bold"], ANSI["gold"]), width, frame_color),
        _ansi_row(_ansi(f"[ AWAKEN ] {awakening}", ANSI["bold"], ANSI["lavender"]), width, frame_color),
        _ansi_row(_ansi(f"[ SIGIL ] {emblem}  [ XP ] {profile.stats.exp_into_level}/{profile.stats.exp_to_next_level}", ANSI["bold"], ANSI["ice"]), width, frame_color),
    ]


def _identity_rows(
    profile: CharacterProfile,
    width: int,
    frame_color: str,
    exp_bar: str,
    emblem: str,
    mode: str,
) -> list[str]:
    stats = profile.stats
    traits = ", ".join(profile.achievements[:3]) if profile.achievements else "No feats awakened yet"

    if mode == "wide":
        trait_lines = _wrap_plain(traits, width - 10)
        rows = [
            _ansi_row(_center_ansi(_ansi(profile.name, ANSI["bold"], ANSI["white"]), width), width, frame_color),
            _ansi_row(_center_ansi(
                _ansi(f"{profile.primary_class} // {profile.rank} {_rank_emblem(profile.rank)} // Lv {stats.level}", ANSI["bold"], ANSI["lavender"]),
                width,
            ), width, frame_color),
            _ansi_row(_center_ansi(_ansi(profile.title, ANSI["soft"]), width), width, frame_color),
            _ansi_row(_pair(
                f"{_ansi('CLASS SIGIL', ANSI['dim'], ANSI['soft'])}  {_ansi(emblem, ANSI['bold'], ANSI['ice'])}",
                f"{_ansi('EXP', ANSI['dim'], ANSI['soft'])}  {_ansi(exp_bar, ANSI['bold'], ANSI['ice'])} {_ansi(f'{stats.exp_into_level}/{stats.exp_to_next_level}', ANSI['white'])} {_ansi(f'· {stats.total_exp} xp', ANSI['dim'], ANSI['gray'])}",
                width,
            ), width, frame_color),
            _ansi_row(f"{_ansi('FEATS', ANSI['dim'], ANSI['soft'])}  {_ansi(trait_lines[0], ANSI['white'])}", width, frame_color),
        ]
        for extra_trait_line in trait_lines[1:]:
            rows.append(_ansi_row(f"{_ansi(' ', ANSI['dim'], ANSI['soft'])}        {_ansi(extra_trait_line, ANSI['white'])}", width, frame_color))
        return rows

    if mode == "compact":
        rows = [
            _ansi_row(_center_ansi(_ansi(profile.name, ANSI["bold"], ANSI["white"]), width), width, frame_color),
            _ansi_row(_ansi(f"IDENTITY  {profile.primary_class} {emblem} // {profile.rank} rank // Lv {stats.level}", ANSI["bold"], ANSI["lavender"]), width, frame_color),
        ]
        rows.extend(_stacked_value_rows("TITLE", profile.title, width, frame_color, value_color=ANSI["soft"]))
        rows.extend(_stacked_value_rows(
            "EXP",
            f"{stats.exp_into_level}/{stats.exp_to_next_level} · total {stats.total_exp} xp",
            width,
            frame_color,
            value_color=ANSI["white"],
        ))
        rows.append(_ansi_row(_center_ansi(_ansi(exp_bar, ANSI["bold"], ANSI["ice"]), width), width, frame_color))
        rows.extend(_stacked_value_rows("FEATS", traits, width, frame_color, value_color=ANSI["white"]))
        return rows

    rows = [
        _ansi_row(_center_ansi(_ansi(profile.name, ANSI["bold"], ANSI["white"]), width), width, frame_color),
    ]
    rows.extend(_stacked_value_rows("CLASS", f"{profile.primary_class} {emblem}", width, frame_color, value_color=ANSI["lavender"]))
    rows.extend(_stacked_value_rows("RANK", f"{profile.rank} rank // Lv {stats.level}", width, frame_color, value_color=ANSI["lavender"]))
    rows.extend(_stacked_value_rows("TITLE", profile.title, width, frame_color, value_color=ANSI["soft"]))
    rows.extend(_stacked_value_rows(
        "EXP",
        f"{stats.exp_into_level}/{stats.exp_to_next_level}",
        width,
        frame_color,
        value_color=ANSI["white"],
    ))
    rows.append(_ansi_row(_center_ansi(_ansi(exp_bar, ANSI["bold"], ANSI["ice"]), width), width, frame_color))
    rows.extend(_stacked_value_rows("TOTAL", f"{stats.total_exp} xp", width, frame_color, value_color=ANSI["gray"]))
    rows.extend(_stacked_value_rows("FEATS", traits, width, frame_color, value_color=ANSI["white"]))
    return rows


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


def render_ansi_panel(profile: CharacterProfile, banner_mode: str = "auto", width: int | None = None) -> str:
    stats = profile.stats
    scan = profile.scan
    rank_color = _rank_color(profile.rank)
    frame_color = ANSI["indigo"]
    width = width or 78
    mode = _resolve_banner_mode(width, banner_mode)
    exp_bar = _bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=16, filled="▰", empty="▱")
    threat = _field_signal(profile)
    awakening = _awakening_stage(profile)
    emblem = _class_emblem(profile.primary_class)
    domains = ", ".join(profile.dominant_domains[:3]) if profile.dominant_domains else "none"
    header_title = f" HERMES SHADOW PROFILE "
    top_rule = "─" * max(4, width + 2 - len(header_title))
    title_banner = [
        _ansi(f"╭{header_title}{top_rule}╮", ANSI["bold"], ANSI["deep_violet"]),
        _ansi(f"│{_center_ansi('persistent archive // status window', width + 2)}│", ANSI["bold"], ANSI["ice"]),
        _ansi(f"╰{'─' * (width + 2)}╯", ANSI["bold"], ANSI["deep_violet"]),
    ]

    lines = [*title_banner, ""]
    lines.extend(_cli_logo_banner(width, frame_color, banner_mode=banner_mode))
    lines.append(_ansi_row("", width, frame_color))
    lines.extend(_top_summary_rows(profile, width, frame_color, threat, awakening, emblem, mode))
    lines.append(_ansi_row("", width, frame_color))
    lines.extend(_identity_rows(profile, width, frame_color, exp_bar, emblem, mode))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section("ATTRIBUTES", width - 2, ANSI["lavender"]), width, frame_color))
    stat_pairs = [(STAT_LABELS[0], STAT_LABELS[3]), (STAT_LABELS[1], STAT_LABELS[4]), (STAT_LABELS[2], STAT_LABELS[5])]
    for (l_label, l_attr), (r_label, r_attr) in stat_pairs:
        left_value = getattr(stats, l_attr)
        right_value = getattr(stats, r_attr)
        left_tier = "S" if left_value >= 18 else "A" if left_value >= 14 else "B" if left_value >= 10 else "C"
        right_tier = "S" if right_value >= 18 else "A" if right_value >= 14 else "B" if right_value >= 10 else "C"
        left_bar = _ansi(_bar(left_value, width=10, filled="■", empty="·"), ANSI["bold"], rank_color if left_value >= 14 else ANSI["ice"])
        right_bar = _ansi(_bar(right_value, width=10, filled="■", empty="·"), ANSI["bold"], rank_color if right_value >= 14 else ANSI["ice"])
        left = f"{_ansi(l_label, ANSI['bold'], ANSI['white'])} {left_value:>2} {left_bar} {_ansi(left_tier, ANSI['bold'], ANSI['soft'])}"
        right = f"{_ansi(r_label, ANSI['bold'], ANSI['white'])} {right_value:>2} {right_bar} {_ansi(right_tier, ANSI['bold'], ANSI['soft'])}"
        lines.append(_ansi_row(_pair(left, right, width), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section("DISCIPLINES", width - 2, ANSI["ice"]), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"techniques {_ansi(str(scan.skill_count), ANSI['bold'], ANSI['white'])} // domains {_ansi(str(len(profile.dominant_domains)), ANSI['bold'], ANSI['white'])}",
        f"records {_ansi(str(scan.session_file_count), ANSI['bold'], ANSI['white'])} // artifacts {_ansi(str(scan.plugin_count), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"memories {_ansi(str(scan.memory_entries), ANSI['bold'], ANSI['white'])} // user bonds {_ansi(str(scan.user_entries), ANSI['bold'], ANSI['white'])}",
        f"rituals {_ansi(str(scan.cron_file_count), ANSI['bold'], ANSI['white'])} // echoes {_ansi(str(scan.log_file_count), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    for wrapped in _wrap_plain(f"dominant domains // {domains}", width - 4):
        lines.append(_ansi_row(_ansi(f"· {wrapped}", ANSI["soft"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section("FIELD REPORT", width - 2, ANSI["violet"]), width, frame_color))
    scar_color = ANSI["red"] if scan.activity.session_error_mentions else ANSI["gray"]
    lines.append(_ansi_row(_pair(
        f"tool traces {_ansi(str(scan.activity.session_tool_mentions), ANSI['bold'], ANSI['white'])}",
        f"hook marks {_ansi(str(scan.activity.plugin_hook_mentions), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"codex depth {_ansi(str(scan.activity.skill_words), ANSI['bold'], ANSI['white'])}",
        f"memory strands {_ansi(str(scan.activity.memory_lines), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"error scars {_ansi(str(scan.activity.session_error_mentions), ANSI['bold'], scar_color)}",
        f"ritual glyphs {_ansi(str(scan.activity.cron_schedule_mentions), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section("ACHIEVEMENTS", width - 2, ANSI["gold"]), width, frame_color))
    if profile.achievements:
        for achievement in profile.achievements[:6]:
            lines.append(_ansi_row(f"{_ansi('◆', ANSI['gold'], ANSI['bold'])} {achievement}", width, frame_color))
    else:
        lines.append(_ansi_row(_ansi("No public achievements yet", ANSI["dim"], ANSI["gray"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section("PROFILE", width - 2, ANSI["soft"]), width, frame_color))
    profile_summary = profile.summary.replace("A read-only shadow profile reconstructed from the ", "Reconstructed from ")
    for wrapped in _wrap_plain(profile_summary, width - 2):
        lines.append(_ansi_row(_ansi(wrapped, ANSI["gray"]), width, frame_color))

    footer = _ansi("╰" + "─" * (width + 2) + "╯", ANSI["bold"], ANSI["deep_violet"])
    lines.append(footer)
    return "\n".join(lines)


def render_ascii_panel(profile: CharacterProfile) -> str:
    return render_ansi_panel(profile)


def render_svg_card(profile: CharacterProfile) -> str:
    stats = profile.stats
    scan = profile.scan
    palette = PALETTE_BY_RANK.get(profile.rank, PALETTE_BY_RANK["Mythic"])
    accent = palette["accent"]
    accent_soft = palette["accent_soft"]
    background = "#09090f"
    panel = "#11131a"
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
        <text x=\"42\" y=\"{y}\" font-size=\"15\" fill=\"{text_dim}\" font-family=\"Inter, Arial, sans-serif\">{escape(label)}</text>
        <rect x=\"105\" y=\"{y - 14}\" width=\"220\" height=\"12\" rx=\"6\" fill=\"#242938\"/>
        <rect x=\"105\" y=\"{y - 14}\" width=\"{fill_width}\" height=\"12\" rx=\"6\" fill=\"{accent}\"/>
        <text x=\"338\" y=\"{y}\" font-size=\"15\" fill=\"{text}\" font-family=\"Inter, Arial, sans-serif\">{value}</text>
        """

    stat_rows = "".join(stat_row(i, label, getattr(stats, attr)) for i, (label, attr) in enumerate(STAT_LABELS))
    achievement_lines = []
    for i, achievement in enumerate(achievements):
        y = 508 + i * 24
        achievement_lines.append(f'<text x="420" y="{y}" font-size="14" fill="{text}" font-family="Inter, Arial, sans-serif">• {escape(achievement)}</text>')
    if not achievement_lines:
        achievement_lines.append(f'<text x="420" y="508" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">• None yet</text>')

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
  </defs>
  <rect width="980" height="720" fill="url(#bg)"/>
  <rect x="28" y="24" width="924" height="672" rx="26" fill="{background}" stroke="{accent}" stroke-width="2"/>
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
