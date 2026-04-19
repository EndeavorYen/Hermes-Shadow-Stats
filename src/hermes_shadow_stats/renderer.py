from __future__ import annotations

import json
import re
from html import escape

from . import i18n
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
    "bronze": {"accent": "#c08457", "accent_soft": "#f1c7a5"},
    "silver": {"accent": "#c9d1d9", "accent_soft": "#edf2f7"},
    "gold": {"accent": "#f5c451", "accent_soft": "#fde8a8"},
    "mythic": {"accent": "#8b5cf6", "accent_soft": "#d8c4ff"},
}


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "white": "\033[97m",
    "soft": "\033[38;5;153m",
    "lavender": "\033[38;5;117m",
    "violet": "\033[38;5;111m",
    "deep_violet": "\033[38;5;69m",
    "gold": "\033[38;5;221m",
    "silver": "\033[38;5;250m",
    "bronze": "\033[38;5;110m",
    "ice": "\033[38;5;117m",
    "indigo": "\033[38;5;69m",
    "red": "\033[38;5;203m",
    "amber": "\033[38;5;215m",
    "mint": "\033[38;5;115m",
    "gray": "\033[38;5;245m",
    "slate": "\033[38;5;103m",
}


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _bar(value: int, max_value: int = 20, width: int = 10, filled: str = "■", empty: str = "□") -> str:
    if max_value <= 0:
        return empty * width
    ratio = max(0.0, min(1.0, value / max_value))
    filled_count = round(ratio * width)
    return filled * filled_count + empty * (width - filled_count)


def _stat_tier(value: int) -> str:
    if value >= 18:
        return "S"
    if value >= 14:
        return "A"
    if value >= 10:
        return "B"
    if value >= 6:
        return "C"
    return "D"


def _tier_color(tier: str) -> str:
    return {
        "S": ANSI["gold"],
        "A": ANSI["lavender"],
        "B": ANSI["ice"],
        "C": ANSI["soft"],
        "D": ANSI["gray"],
    }.get(tier, ANSI["white"])


def _vital_color(ratio: float) -> str:
    if ratio >= 0.75:
        return ANSI["mint"]
    if ratio >= 0.5:
        return ANSI["ice"]
    if ratio >= 0.25:
        return ANSI["amber"]
    return ANSI["red"]


def _rank_color(rank_id: str) -> str:
    return {
        "bronze": ANSI["bronze"],
        "silver": ANSI["silver"],
        "gold": ANSI["gold"],
        "mythic": ANSI["lavender"],
    }.get(rank_id, ANSI["violet"])


def _rank_emblem(rank_id: str) -> str:
    return {"bronze": "+", "silver": "*", "gold": "#", "mythic": "@"}.get(rank_id, "+")


def _class_emblem(class_id: str) -> str:
    return {
        "toolsmith": "#",
        "code_alchemist": "*",
        "ops_summoner": "~",
        "research_ranger": ">",
        "memory_weaver": "&",
        "workflow_scribe": "=",
        "model_hunter": "@",
        "shadow_commander": "!",
        "rune_artisan": "%",
        "signal_duelist": "^",
        "protocol_walker": "$",
        "adaptive_agent": "+",
        "hunter_candidate": "-",
    }.get(class_id, "+")


def _ansi(text: str, *codes: str) -> str:
    return "".join(codes) + text + ANSI["reset"]


def _visible_width(text: str) -> int:
    """Return display column width (CJK fullwidth chars count as 2)."""
    stripped = _ANSI_RE.sub("", text)
    width = 0
    for ch in stripped:
        cp = ord(ch)
        if cp == 0:
            continue
        if (
            0x1100 <= cp <= 0x115F
            or 0x2E80 <= cp <= 0x303E
            or 0x3041 <= cp <= 0x33FF
            or 0x3400 <= cp <= 0x4DBF
            or 0x4E00 <= cp <= 0x9FFF
            or 0xA000 <= cp <= 0xA4CF
            or 0xAC00 <= cp <= 0xD7A3
            or 0xF900 <= cp <= 0xFAFF
            or 0xFE30 <= cp <= 0xFE4F
            or 0xFF00 <= cp <= 0xFF60
            or 0xFFE0 <= cp <= 0xFFE6
        ):
            width += 2
        else:
            width += 1
    return width


def _truncate_ansi(text: str, width: int) -> str:
    result: list[str] = []
    visible = 0
    for token in re.findall(r"\x1b\[[0-9;]*m|.", text):
        if token.startswith("\x1b"):
            result.append(token)
            continue
        token_w = _visible_width(token)
        if visible + token_w > width:
            break
        result.append(token)
        visible += token_w
    if result and not result[-1].endswith(ANSI["reset"]):
        result.append(ANSI["reset"])
    return "".join(result)


def _pad_to(text: str, width: int) -> str:
    visible = _visible_width(text)
    if visible >= width:
        return _truncate_ansi(text, width)
    return f"{text}{' ' * (width - visible)}"


def _ansi_row(text: str, width: int = 76, border_color: str | None = None) -> str:
    border = _ansi("│", border_color or ANSI["deep_violet"], ANSI["dim"])
    if _visible_width(text) > width:
        text = _truncate_ansi(text, width)
    visible = _visible_width(text)
    return f"{border} {text}{' ' * max(0, width - visible)} {border}"


def _ansi_section(title: str, width: int = 76, color: str | None = None) -> str:
    color = color or ANSI["lavender"]
    body = f" {title} "
    line_w = max(4, width - _visible_width(body) - 2)
    return _ansi(f"╞{body}{'═' * line_w}╡", ANSI["bold"], color)


def _wrap_plain(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if _visible_width(current) + 1 + _visible_width(word) <= width:
            current += f" {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _center_ansi(text: str, width: int) -> str:
    if _visible_width(text) > width:
        text = _truncate_ansi(text, width)
    visible = _visible_width(text)
    left_pad = max(0, (width - visible) // 2)
    right_pad = max(0, width - visible - left_pad)
    return f"{' ' * left_pad}{text}{' ' * right_pad}"


def _pair(left: str, right: str, width: int, gap: int = 2) -> str:
    left_width = (width - gap) // 2
    right_width = width - gap - left_width
    return f"{_pad_to(left, left_width)}{' ' * gap}{_pad_to(right, right_width)}"


def _resolve_banner_mode(width: int, banner_mode: str = "auto") -> str:
    if banner_mode != "auto":
        return banner_mode
    if width >= 76:
        return "wide"
    if width >= 62:
        return "compact"
    return "minimal"


def _system_window_banner(width: int, lang: str, mode: str) -> list[str]:
    title = i18n.t_label(lang, "title_top")
    subtitle = i18n.t_label(lang, "title_subtitle")
    mode_tag = i18n.t_label(lang, "banner_mode_tag")
    inner = width + 2
    title_text = _ansi(f"  ◆  {title}  ◆  ", ANSI["bold"], ANSI["white"])
    title_visible = _visible_width(title_text)
    title_padding = max(2, inner - title_visible)
    left_pad = title_padding // 2
    right_pad = title_padding - left_pad
    subtitle_visible_text = (
        f"  ◇ {subtitle}"
        if mode == "wide"
        else f"  {subtitle}"
    )
    if mode == "wide":
        subtitle_visible_text += f"   ·   {mode_tag} ◇  "
    else:
        subtitle_visible_text += f"  · {mode_tag}  "
    subtitle_visible = _visible_width(subtitle_visible_text)
    subtitle_padding = max(2, inner - subtitle_visible)
    sub_left = subtitle_padding // 2
    sub_right = subtitle_padding - sub_left

    top = _ansi(
        f"╔{'═' * left_pad}{title_text}{'═' * right_pad}╗",
        ANSI["bold"],
        ANSI["deep_violet"],
    )
    sub = _ansi(
        f"║{' ' * sub_left}{_ansi(subtitle_visible_text, ANSI['ice'])}{' ' * sub_right}║",
        ANSI["bold"],
        ANSI["deep_violet"],
    )
    bottom = _ansi(f"╚{'═' * inner}╝", ANSI["bold"], ANSI["deep_violet"])
    return [top, sub, bottom]


def _compute_vitals(profile: CharacterProfile) -> list[tuple[str, str, int, int, str]]:
    """Return [(label_key, label, current, maximum, hint), ...]."""
    activity = profile.scan.activity
    scan = profile.scan
    lang = profile.lang

    hp_max = 100
    hp_loss = min(70, activity.session_error_mentions * 3)
    hp_cur = max(8, hp_max - hp_loss)

    mp_max = 100
    mp_cur = min(mp_max, 12 + scan.skill_count * 4 + min(60, activity.skill_words // 30))

    sp_max = 100
    sp_cur = min(sp_max, 18 + min(60, activity.session_tool_mentions) + min(15, scan.session_file_count // 4))

    return [
        ("hp", i18n.t_label(lang, "vital_hp_label"), hp_cur, hp_max, i18n.t_label(lang, "vital_hp_hint")),
        ("mp", i18n.t_label(lang, "vital_mp_label"), mp_cur, mp_max, i18n.t_label(lang, "vital_mp_hint")),
        ("sp", i18n.t_label(lang, "vital_sp_label"), sp_cur, sp_max, i18n.t_label(lang, "vital_sp_hint")),
    ]


def render_markdown(profile: CharacterProfile) -> str:
    stats = profile.stats
    scan = profile.scan
    lang = profile.lang
    exp_bar = _bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=16, filled="█", empty="░")
    vitals = _compute_vitals(profile)

    threat = i18n.t_threat(lang, profile.threat_id)
    awakening = i18n.t_awakening(lang, profile.awakening_id)

    lines = [
        f"# {i18n.t_label(lang, 'title_top')}",
        "",
        f"> {i18n.t_label(lang, 'title_subtitle')}",
        "",
        f"## {_rank_emblem(profile.rank_id)} {i18n.t_section(lang, 'profile')}",
        f"- **{i18n.t_label(lang, 'status')}**: {profile.name}",
        f"- **{i18n.t_label(lang, 'class_sigil')}**: {profile.primary_class} — {profile.title}",
        f"- **{i18n.t_label(lang, 'threat_class')}**: {threat}",
        f"- **{i18n.t_label(lang, 'awakening')}**: {awakening}",
        f"- **{i18n.t_label(lang, 'level_short')}**: {stats.level} ({profile.rank})",
        f"- **{i18n.t_label(lang, 'exp')}**: `{exp_bar}` {stats.exp_into_level}/{stats.exp_to_next_level} _(total: {stats.total_exp})_",
        "",
        f"## {i18n.t_section(lang, 'vitals')}",
    ]
    for _, label, current, maximum, hint in vitals:
        gauge = _bar(current, maximum, width=16, filled="█", empty="░")
        lines.append(f"- **{label}** `{gauge}` {current}/{maximum} _({hint})_")

    lines.extend(["", f"## {i18n.t_section(lang, 'attributes')}"])
    for label, attr in STAT_LABELS:
        value = getattr(stats, attr)
        tier = _stat_tier(value)
        lines.append(f"- **{label}** {value:>2}  `{_bar(value)}`  [{tier}]")

    lines.extend([
        "",
        f"## {i18n.t_section(lang, 'equipment')}",
    ])
    if scan.plugin_names:
        slot_keys = [("main_slot", "main_hint"), ("aux_slot", "aux_hint"), ("sigil_slot", "sigil_hint")]
        for index, (slot_key, _) in enumerate(slot_keys):
            slot_label = i18n.t_label(lang, slot_key)
            if index < len(scan.plugin_names):
                lines.append(f"- **{slot_label}** — {scan.plugin_names[index]}")
            else:
                lines.append(f"- **{slot_label}** — _{i18n.t_label(lang, 'empty_slot')}_")
        if len(scan.plugin_names) > len(slot_keys):
            extras = ", ".join(scan.plugin_names[len(slot_keys):])
            lines.append(f"- **{i18n.t_label(lang, 'stowed')}** — {extras}")
    else:
        lines.append(f"- {i18n.t_label(lang, 'no_artifacts')}")

    lines.extend(["", f"## {i18n.t_section(lang, 'active_buffs')}"])
    if profile.buff_ids:
        for buff_id in profile.buff_ids:
            buff = i18n.t_buff(lang, buff_id)
            glyph = "✗" if buff_id == "wounded" else "✦"
            lines.append(f"- {glyph} **{buff['name']}** `{buff['modifier'].strip()}` — {buff['hint']}")
    else:
        lines.append(f"- {i18n.t_label(lang, 'no_buffs')}")

    lines.extend(["", f"## {i18n.t_section(lang, 'achievements')}"])
    if profile.achievements:
        lines.extend(f"- {achievement}" for achievement in profile.achievements)
    else:
        lines.append(f"- {i18n.t_label(lang, 'no_achievements')}")

    if scan.recent_sessions:
        lines.extend(["", f"## {i18n.t_label(lang, 'recent_expeditions')}"])
        for session in scan.recent_sessions[:5]:
            lines.append(f"- {session}")

    lines.extend(["", f"## {i18n.t_section(lang, 'profile')}", profile.summary])
    return "\n".join(lines)


def _identity_block(profile: CharacterProfile, width: int, frame_color: str, lang: str, exp_bar: str, emblem: str, mode: str) -> list[str]:
    stats = profile.stats
    lvl_label = i18n.t_label(lang, "level_compact")
    exp_label = i18n.t_label(lang, "exp")
    feats_label = i18n.t_label(lang, "feats")
    traits = ", ".join(profile.achievements[:3]) if profile.achievements else i18n.t_label(lang, "no_feats")

    rows: list[str] = [
        _ansi_row(_center_ansi(_ansi(profile.name, ANSI["bold"], ANSI["white"]), width), width, frame_color),
        _ansi_row(_center_ansi(
            _ansi(f"{profile.primary_class} {emblem}  //  {profile.rank} {_rank_emblem(profile.rank_id)}  //  {lvl_label} {stats.level}", ANSI["bold"], ANSI["lavender"]),
            width,
        ), width, frame_color),
        _ansi_row(_center_ansi(_ansi(profile.title, ANSI["soft"]), width), width, frame_color),
    ]

    if mode == "wide":
        exp_text = (
            f"{_ansi(exp_label, ANSI['dim'], ANSI['soft'])}  "
            f"{_ansi(exp_bar, ANSI['bold'], ANSI['ice'])} "
            f"{_ansi(f'{stats.exp_into_level}/{stats.exp_to_next_level}', ANSI['white'])} "
            f"{_ansi(f'· {stats.total_exp} xp', ANSI['dim'], ANSI['gray'])}"
        )
        rows.append(_ansi_row(_center_ansi(exp_text, width), width, frame_color))
        trait_lines = _wrap_plain(traits, width - _visible_width(feats_label) - 2)
        rows.append(_ansi_row(f"{_ansi(feats_label, ANSI['dim'], ANSI['soft'])}  {_ansi(trait_lines[0], ANSI['white'])}", width, frame_color))
        for extra in trait_lines[1:]:
            rows.append(_ansi_row(f"{' ' * (_visible_width(feats_label) + 2)}{_ansi(extra, ANSI['white'])}", width, frame_color))
    else:
        rows.append(_ansi_row(_center_ansi(_ansi(exp_bar, ANSI["bold"], ANSI["ice"]), width), width, frame_color))
        rows.append(_ansi_row(
            _center_ansi(_ansi(f"{exp_label} {stats.exp_into_level}/{stats.exp_to_next_level} · total {stats.total_exp} xp", ANSI["white"]), width),
            width, frame_color,
        ))
        for line in _wrap_plain(traits, width - _visible_width(feats_label) - 2):
            rows.append(_ansi_row(f"{_ansi(feats_label, ANSI['dim'], ANSI['soft'])}  {_ansi(line, ANSI['white'])}", width, frame_color))
    return rows


def _top_summary(profile: CharacterProfile, width: int, frame_color: str, lang: str, mode: str) -> list[str]:
    stats = profile.stats
    threat = i18n.t_threat(lang, profile.threat_id)
    awakening = i18n.t_awakening(lang, profile.awakening_id)
    emblem = _class_emblem(profile.primary_class_id)
    status_text = f"[ {i18n.t_label(lang, 'status')} ] {profile.rank} · {i18n.t_label(lang, 'level_short')} {stats.level}"
    threat_text = f"[ {i18n.t_label(lang, 'threat_class')} ] {threat}"
    awakening_text = f"[ {i18n.t_label(lang, 'awakening')} ] {awakening}"
    sigil_text = f"[ {i18n.t_label(lang, 'class_sigil')} ] {profile.primary_class} {emblem}"
    if mode == "wide":
        return [
            _ansi_row(_pair(_ansi(status_text, ANSI["bold"], ANSI["ice"]), _ansi(threat_text, ANSI["bold"], ANSI["gold"]), width), width, frame_color),
            _ansi_row(_pair(_ansi(awakening_text, ANSI["bold"], ANSI["lavender"]), _ansi(sigil_text, ANSI["bold"], ANSI["soft"]), width), width, frame_color),
        ]
    return [
        _ansi_row(_ansi(status_text, ANSI["bold"], ANSI["ice"]), width, frame_color),
        _ansi_row(_ansi(threat_text, ANSI["bold"], ANSI["gold"]), width, frame_color),
        _ansi_row(_ansi(awakening_text, ANSI["bold"], ANSI["lavender"]), width, frame_color),
        _ansi_row(_ansi(sigil_text, ANSI["bold"], ANSI["soft"]), width, frame_color),
    ]


def render_ansi_panel(profile: CharacterProfile, banner_mode: str = "auto", width: int | None = None) -> str:
    stats = profile.stats
    scan = profile.scan
    lang = i18n.normalize_lang(profile.lang)
    frame_color = ANSI["indigo"]
    width = width or 78
    mode = _resolve_banner_mode(width, banner_mode)
    emblem = _class_emblem(profile.primary_class_id)

    lines: list[str] = []
    lines.extend(_system_window_banner(width, lang, mode))
    lines.append("")
    lines.extend(_top_summary(profile, width, frame_color, lang, mode))
    lines.append(_ansi_row("", width, frame_color))

    bar_w = 18 if width >= 70 else 12
    exp_bar = _bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=16, filled="▰", empty="▱")
    lines.extend(_identity_block(profile, width, frame_color, lang, exp_bar, emblem, mode))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "vitals"), width - 2, ANSI["ice"]), width, frame_color))
    for _, label, current, maximum, hint in _compute_vitals(profile):
        ratio = current / maximum if maximum else 0
        bar = _ansi(_bar(current, maximum, width=bar_w, filled="▰", empty="▱"), ANSI["bold"], _vital_color(ratio))
        readout = (
            f"{_ansi(label, ANSI['bold'], ANSI['white'])}  {bar} "
            f"{_ansi(f'{current:>3}/{maximum}', ANSI['white'])}  "
            f"{_ansi(hint, ANSI['dim'], ANSI['gray'])}"
        )
        lines.append(_ansi_row(readout, width, frame_color))
    xp_ratio = stats.exp_into_level / max(stats.exp_to_next_level, 1)
    xp_bar_color = _ansi(_bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=bar_w, filled="▰", empty="▱"), ANSI["bold"], _vital_color(0.5 + xp_ratio / 2))
    next_level_text = i18n.t_label(lang, "next_level").format(level=stats.level + 1, total=stats.total_exp)
    lines.append(_ansi_row(
        f"{_ansi(i18n.t_label(lang, 'vital_xp_label'), ANSI['bold'], ANSI['white'])}  {xp_bar_color} "
        f"{_ansi(f'{stats.exp_into_level:>3}/{stats.exp_to_next_level}', ANSI['white'])}  "
        f"{_ansi(next_level_text, ANSI['dim'], ANSI['gray'])}",
        width, frame_color,
    ))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "attributes"), width - 2, ANSI["lavender"]), width, frame_color))
    stat_pairs = [(STAT_LABELS[0], STAT_LABELS[3]), (STAT_LABELS[1], STAT_LABELS[4]), (STAT_LABELS[2], STAT_LABELS[5])]
    for (l_label, l_attr), (r_label, r_attr) in stat_pairs:
        lv = getattr(stats, l_attr)
        rv = getattr(stats, r_attr)
        lt = _stat_tier(lv)
        rt = _stat_tier(rv)
        lb = _ansi(_bar(lv, width=10, filled="■", empty="·"), ANSI["bold"], _tier_color(lt))
        rb = _ansi(_bar(rv, width=10, filled="■", empty="·"), ANSI["bold"], _tier_color(rt))
        left = f"{_ansi(l_label, ANSI['bold'], ANSI['white'])} {lv:>2} {lb} [{_ansi(lt, ANSI['bold'], _tier_color(lt))}]"
        right = f"{_ansi(r_label, ANSI['bold'], ANSI['white'])} {rv:>2} {rb} [{_ansi(rt, ANSI['bold'], _tier_color(rt))}]"
        lines.append(_ansi_row(_pair(left, right, width), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "equipment"), width - 2, ANSI["gold"]), width, frame_color))
    slot_specs = [
        ("main_slot", "main_hint", "◆"),
        ("aux_slot", "aux_hint", "◇"),
        ("sigil_slot", "sigil_hint", "✦"),
    ]
    show_hints = width >= 70
    for index, (slot_key, hint_key, glyph) in enumerate(slot_specs):
        slot_label = i18n.t_label(lang, slot_key)
        plugin_name = scan.plugin_names[index] if index < len(scan.plugin_names) else None
        if plugin_name:
            value = _ansi(plugin_name, ANSI["bold"], ANSI["white"])
            status = _ansi(f"[ {i18n.t_label(lang, 'bound')} ]", ANSI["bold"], ANSI["ice"])
        else:
            value = _ansi(i18n.t_label(lang, "empty_slot"), ANSI["dim"], ANSI["gray"])
            status = _ansi(f"[ {i18n.t_label(lang, 'empty')} ]", ANSI["dim"], ANSI["gray"])
        slot_text = f"{_ansi(f'{glyph} {slot_label} ', ANSI['bold'], ANSI['gold'])} {value}"
        if show_hints:
            hint = f"{status} {_ansi(i18n.t_label(lang, hint_key), ANSI['dim'], ANSI['gray'])}"
            lines.append(_ansi_row(_pair(slot_text, hint, width), width, frame_color))
        else:
            lines.append(_ansi_row(f"{slot_text}  {status}", width, frame_color))
    extra = max(0, len(scan.plugin_names) - len(slot_specs))
    if extra:
        overflow = ", ".join(scan.plugin_names[len(slot_specs):len(slot_specs) + 4])
        lines.append(_ansi_row(_ansi(f"  + {extra} {i18n.t_label(lang, 'stowed')} // {overflow}", ANSI["dim"], ANSI["gray"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "disciplines"), width - 2, ANSI["ice"]), width, frame_color))
    domains = ", ".join(profile.dominant_domains[:3]) if profile.dominant_domains else "—"
    lines.append(_ansi_row(_pair(
        f"{i18n.t_label(lang, 'techniques')} {_ansi(str(scan.skill_count), ANSI['bold'], ANSI['white'])} // {i18n.t_label(lang, 'domains')} {_ansi(str(len(profile.dominant_domains)), ANSI['bold'], ANSI['white'])}",
        f"{i18n.t_label(lang, 'records')} {_ansi(str(scan.session_file_count), ANSI['bold'], ANSI['white'])} // {i18n.t_label(lang, 'artifacts')} {_ansi(str(scan.plugin_count), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"{i18n.t_label(lang, 'memories')} {_ansi(str(scan.memory_entries), ANSI['bold'], ANSI['white'])} // {i18n.t_label(lang, 'user_bonds')} {_ansi(str(scan.user_entries), ANSI['bold'], ANSI['white'])}",
        f"{i18n.t_label(lang, 'rituals')} {_ansi(str(scan.cron_file_count), ANSI['bold'], ANSI['white'])} // {i18n.t_label(lang, 'echoes')} {_ansi(str(scan.log_file_count), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    for wrapped in _wrap_plain(f"{i18n.t_label(lang, 'dominant_domains')} // {domains}", width - 4):
        lines.append(_ansi_row(_ansi(f"· {wrapped}", ANSI["soft"]), width, frame_color))
    if scan.skill_categories:
        max_cat = max(scan.skill_categories.values())
        sorted_cats = sorted(scan.skill_categories.items(), key=lambda kv: (-kv[1], kv[0]))
        for category, count in sorted_cats[:4]:
            cat_bar = _ansi(_bar(count, max(max_cat, 1), width=12, filled="▰", empty="▱"), ANSI["bold"], ANSI["lavender"])
            label = _pad_to(_ansi(category, ANSI["white"]), 22)
            count_text = _ansi(f"{count:>2}", ANSI["bold"], ANSI["white"])
            lines.append(_ansi_row(f"  {label}{cat_bar} {count_text}", width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "active_buffs"), width - 2, ANSI["violet"]), width, frame_color))
    if profile.buff_ids:
        for buff_id in profile.buff_ids:
            buff = i18n.t_buff(lang, buff_id)
            glyph = "✗" if buff_id == "wounded" else "✦"
            glyph_color = ANSI["red"] if buff_id == "wounded" else ANSI["gold"]
            mod_color = ANSI["red"] if buff["modifier"].startswith("-") else ANSI["ice"]
            name_pad = 18 if width >= 70 else 14
            row = (
                f"{_ansi(glyph, ANSI['bold'], glyph_color)} "
                f"{_pad_to(_ansi(buff['name'], ANSI['bold'], ANSI['white']), name_pad)} "
                f"{_ansi(buff['modifier'], ANSI['bold'], mod_color)}"
            )
            if width >= 70:
                row += f"  {_ansi('‧ ' + buff['hint'], ANSI['dim'], ANSI['gray'])}"
            lines.append(_ansi_row(row, width, frame_color))
    else:
        lines.append(_ansi_row(_ansi(f"· {i18n.t_label(lang, 'no_buffs')}", ANSI["dim"], ANSI["gray"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "field_report"), width - 2, ANSI["violet"]), width, frame_color))
    scar_color = ANSI["red"] if scan.activity.session_error_mentions else ANSI["gray"]
    lines.append(_ansi_row(_pair(
        f"{i18n.t_label(lang, 'tool_traces')} {_ansi(str(scan.activity.session_tool_mentions), ANSI['bold'], ANSI['white'])}",
        f"{i18n.t_label(lang, 'hook_marks')} {_ansi(str(scan.activity.plugin_hook_mentions), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"{i18n.t_label(lang, 'codex_depth')} {_ansi(str(scan.activity.skill_words), ANSI['bold'], ANSI['white'])}",
        f"{i18n.t_label(lang, 'memory_strands')} {_ansi(str(scan.activity.memory_lines), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    lines.append(_ansi_row(_pair(
        f"{i18n.t_label(lang, 'error_scars')} {_ansi(str(scan.activity.session_error_mentions), ANSI['bold'], scar_color)}",
        f"{i18n.t_label(lang, 'ritual_glyphs')} {_ansi(str(scan.activity.cron_schedule_mentions), ANSI['bold'], ANSI['white'])}",
        width,
    ), width, frame_color))
    if scan.recent_sessions:
        recent = ", ".join(scan.recent_sessions[:3])
        for wrapped in _wrap_plain(f"{i18n.t_label(lang, 'recent_expeditions')} ▸ {recent}", width - 4):
            lines.append(_ansi_row(_ansi(f"· {wrapped}", ANSI["dim"], ANSI["soft"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "achievements"), width - 2, ANSI["gold"]), width, frame_color))
    if profile.achievements:
        for achievement in profile.achievements[:6]:
            lines.append(_ansi_row(f"{_ansi('◆', ANSI['gold'], ANSI['bold'])} {achievement}", width, frame_color))
    else:
        lines.append(_ansi_row(_ansi(i18n.t_label(lang, "no_achievements"), ANSI["dim"], ANSI["gray"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "realm"), width - 2, ANSI["soft"]), width, frame_color))
    home_path = scan.hermes_home
    home_label = home_path.rstrip("/").split("/")[-1] or home_path
    lines.append(_ansi_row(_pair(
        f"{_ansi('◷ ' + i18n.t_label(lang, 'realm_word'), ANSI['dim'], ANSI['soft'])}  {_ansi(home_label, ANSI['bold'], ANSI['white'])}",
        f"{_ansi('◊ ' + i18n.t_label(lang, 'profiles_word'), ANSI['dim'], ANSI['soft'])}  {_ansi(str(scan.profile_count), ANSI['bold'], ANSI['white'])} {i18n.t_label(lang, 'bound_word')}",
        width,
    ), width, frame_color))
    for wrapped in _wrap_plain(f"{i18n.t_label(lang, 'path_word')} // {home_path}", width - 4):
        lines.append(_ansi_row(_ansi(f"  {wrapped}", ANSI["dim"], ANSI["gray"]), width, frame_color))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "profile"), width - 2, ANSI["soft"]), width, frame_color))
    for wrapped in _wrap_plain(profile.summary, width - 2):
        lines.append(_ansi_row(_ansi(wrapped, ANSI["gray"]), width, frame_color))

    footer = _ansi("╰" + "─" * (width + 2) + "╯", ANSI["bold"], ANSI["deep_violet"])
    lines.append(footer)
    return "\n".join(lines)


def render_ascii_panel(profile: CharacterProfile) -> str:
    return render_ansi_panel(profile)


def render_svg_card(profile: CharacterProfile) -> str:
    stats = profile.stats
    scan = profile.scan
    lang = profile.lang
    palette = PALETTE_BY_RANK.get(profile.rank_id, PALETTE_BY_RANK["mythic"])
    accent = palette["accent"]
    accent_soft = palette["accent_soft"]
    background = "#09090f"
    panel = "#11131a"
    text = "#f5f7fb"
    text_dim = "#aab2c5"
    danger = "#ef4444"

    exp_width = int(420 * (stats.exp_into_level / max(stats.exp_to_next_level, 1)))
    domains = ", ".join(profile.dominant_domains[:3]) if profile.dominant_domains else "—"
    achievements = profile.achievements[:6]
    threat = i18n.t_threat(lang, profile.threat_id)

    def stat_row(index: int, label: str, value: int) -> str:
        y = 222 + index * 36
        fill_width = int((value / 20) * 220)
        return (
            f'<text x="42" y="{y}" font-size="15" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(label)}</text>'
            f'<rect x="105" y="{y - 14}" width="220" height="12" rx="6" fill="#242938"/>'
            f'<rect x="105" y="{y - 14}" width="{fill_width}" height="12" rx="6" fill="{accent}"/>'
            f'<text x="338" y="{y}" font-size="15" fill="{text}" font-family="Inter, Arial, sans-serif">{value}</text>'
        )

    stat_rows = "".join(stat_row(i, label, getattr(stats, attr)) for i, (label, attr) in enumerate(STAT_LABELS))
    achievement_lines: list[str] = []
    for i, achievement in enumerate(achievements):
        y = 508 + i * 24
        achievement_lines.append(f'<text x="420" y="{y}" font-size="14" fill="{text}" font-family="Inter, Arial, sans-serif">• {escape(achievement)}</text>')
    if not achievement_lines:
        achievement_lines.append(f'<text x="420" y="508" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">• {escape(i18n.t_label(lang, "no_achievements"))}</text>')

    title_top = i18n.t_label(lang, "title_top")
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
  <text x="42" y="58" font-size="16" fill="{accent_soft}" font-family="Inter, Arial, sans-serif">{escape(title_top)}</text>
  <text x="42" y="84" font-size="28" fill="{text}" font-family="Inter, Arial, sans-serif" font-weight="700">{escape(i18n.t_section(lang, "profile"))}</text>
  <text x="700" y="58" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "threat_class"))}</text>
  <text x="700" y="84" font-size="22" fill="{accent_soft}" font-family="Inter, Arial, sans-serif" font-weight="700">{escape(threat)}</text>
  <rect x="42" y="126" width="330" height="540" rx="20" fill="{panel}" stroke="#232838"/>
  <rect x="390" y="126" width="262" height="270" rx="20" fill="{panel}" stroke="#232838"/>
  <rect x="670" y="126" width="262" height="270" rx="20" fill="{panel}" stroke="#232838"/>
  <rect x="390" y="414" width="542" height="252" rx="20" fill="{panel}" stroke="#232838"/>
  <text x="42" y="160" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "status"))}</text>
  <text x="42" y="198" font-size="34" fill="{text}" font-family="Inter, Arial, sans-serif" font-weight="700">{escape(profile.name)}</text>
  <text x="42" y="228" font-size="18" fill="{accent_soft}" font-family="Inter, Arial, sans-serif">{escape(profile.title)}</text>
  <text x="42" y="278" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "class_sigil"))}</text>
  <text x="42" y="304" font-size="22" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(profile.primary_class)}</text>
  <text x="200" y="278" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "rank_word").upper())}</text>
  <text x="200" y="304" font-size="22" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(profile.rank)}</text>
  <text x="42" y="352" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "level_short").upper())}</text>
  <text x="42" y="384" font-size="42" fill="{accent_soft}" font-family="Inter, Arial, sans-serif" font-weight="700">{stats.level}</text>
  <text x="150" y="352" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "exp"))}</text>
  <text x="150" y="384" font-size="24" fill="{text}" font-family="Inter, Arial, sans-serif">{stats.total_exp}</text>
  <rect x="42" y="442" width="280" height="16" rx="8" fill="#242938"/>
  <rect x="42" y="442" width="{exp_width}" height="16" rx="8" fill="url(#accentGlow)"/>
  <text x="42" y="480" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{stats.exp_into_level}/{stats.exp_to_next_level}</text>
  {stat_rows}
  <text x="410" y="160" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_section(lang, "disciplines"))}</text>
  <text x="410" y="194" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "techniques"))}: {scan.skill_count}</text>
  <text x="410" y="222" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "dominant_domains"))}: {escape(domains)}</text>
  <text x="410" y="250" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "memories"))}: {scan.memory_entries}</text>
  <text x="410" y="278" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "user_bonds"))}: {scan.user_entries}</text>
  <text x="410" y="306" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "records"))}: {scan.session_file_count}</text>
  <text x="410" y="334" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "rituals"))}: {scan.cron_file_count}</text>
  <text x="410" y="362" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "artifacts"))}: {scan.plugin_count}</text>
  <text x="690" y="160" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_section(lang, "field_report"))}</text>
  <text x="690" y="194" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "tool_traces"))}: {scan.activity.session_tool_mentions}</text>
  <text x="690" y="222" font-size="16" fill="{danger if scan.activity.session_error_mentions else text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "error_scars"))}: {scan.activity.session_error_mentions}</text>
  <text x="690" y="250" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "codex_depth"))}: {scan.activity.skill_words}</text>
  <text x="690" y="278" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "hook_marks"))}: {scan.activity.plugin_hook_mentions}</text>
  <text x="690" y="306" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "ritual_glyphs"))}: {scan.activity.cron_schedule_mentions}</text>
  <text x="690" y="334" font-size="16" fill="{text}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_label(lang, "memory_strands"))}: {scan.activity.memory_lines}</text>
  <text x="410" y="448" font-size="14" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(i18n.t_section(lang, "achievements"))}</text>
  {''.join(achievement_lines)}
  <text x="410" y="658" font-size="13" fill="{text_dim}" font-family="Inter, Arial, sans-serif">{escape(profile.summary[:92])}</text>
</svg>
"""


def render_json(profile: CharacterProfile) -> str:
    return json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Phase 1 additions — per-tab renderers for TUI and ``--format tabs``
#
# Each per-tab function returns a self-contained ANSI string for one RPG tab.
# ``telemetry`` is accepted but ignored in Phase 1; Phase 3 populates it from
# ``state.db`` (``SessionStats`` / ``TokenUsage`` / ``ToolUsage`` etc.).
#
# ``render_ansi_panel`` above remains unchanged and stays the authoritative
# single-panel layout for ``--format ansi`` (parity-tested in
# ``tests/test_renderer_parity.py``).
# ---------------------------------------------------------------------------


TAB_IDS: list[str] = [
    "status",
    "equipment",
    "codex",
    "journal",
    "chronicle",
    "rituals",
    "effects",
    "diagnostics",
]


def _frame_color() -> str:
    return ANSI["indigo"]


def _status_rows(profile: CharacterProfile, width: int, lang: str, mode: str) -> list[str]:
    stats = profile.stats
    frame_color = _frame_color()
    emblem = _class_emblem(profile.primary_class_id)
    bar_w = 18 if width >= 70 else 12
    exp_bar = _bar(
        stats.exp_into_level,
        max(stats.exp_to_next_level, 1),
        width=16,
        filled="▰",
        empty="▱",
    )
    lines: list[str] = []
    lines.extend(_top_summary(profile, width, frame_color, lang, mode))
    lines.append(_ansi_row("", width, frame_color))
    lines.extend(_identity_block(profile, width, frame_color, lang, exp_bar, emblem, mode))

    lines.append(_ansi_row("", width, frame_color))
    lines.append(
        _ansi_row(_ansi_section(i18n.t_section(lang, "vitals"), width - 2, ANSI["ice"]), width, frame_color)
    )
    for _, label, current, maximum, hint in _compute_vitals(profile):
        ratio = current / maximum if maximum else 0
        bar = _ansi(
            _bar(current, maximum, width=bar_w, filled="▰", empty="▱"),
            ANSI["bold"],
            _vital_color(ratio),
        )
        readout = (
            f"{_ansi(label, ANSI['bold'], ANSI['white'])}  {bar} "
            f"{_ansi(f'{current:>3}/{maximum}', ANSI['white'])}  "
            f"{_ansi(hint, ANSI['dim'], ANSI['gray'])}"
        )
        lines.append(_ansi_row(readout, width, frame_color))
    xp_ratio = stats.exp_into_level / max(stats.exp_to_next_level, 1)
    xp_bar_color = _ansi(
        _bar(stats.exp_into_level, max(stats.exp_to_next_level, 1), width=bar_w, filled="▰", empty="▱"),
        ANSI["bold"],
        _vital_color(0.5 + xp_ratio / 2),
    )
    next_level_text = i18n.t_label(lang, "next_level").format(level=stats.level + 1, total=stats.total_exp)
    lines.append(
        _ansi_row(
            f"{_ansi(i18n.t_label(lang, 'vital_xp_label'), ANSI['bold'], ANSI['white'])}  {xp_bar_color} "
            f"{_ansi(f'{stats.exp_into_level:>3}/{stats.exp_to_next_level}', ANSI['white'])}  "
            f"{_ansi(next_level_text, ANSI['dim'], ANSI['gray'])}",
            width,
            frame_color,
        )
    )

    lines.append(_ansi_row("", width, frame_color))
    lines.append(
        _ansi_row(_ansi_section(i18n.t_section(lang, "attributes"), width - 2, ANSI["lavender"]), width, frame_color)
    )
    stat_pairs = [(STAT_LABELS[0], STAT_LABELS[3]), (STAT_LABELS[1], STAT_LABELS[4]), (STAT_LABELS[2], STAT_LABELS[5])]
    for (l_label, l_attr), (r_label, r_attr) in stat_pairs:
        lv = getattr(stats, l_attr)
        rv = getattr(stats, r_attr)
        lt = _stat_tier(lv)
        rt = _stat_tier(rv)
        lb = _ansi(_bar(lv, width=10, filled="■", empty="·"), ANSI["bold"], _tier_color(lt))
        rb = _ansi(_bar(rv, width=10, filled="■", empty="·"), ANSI["bold"], _tier_color(rt))
        left = f"{_ansi(l_label, ANSI['bold'], ANSI['white'])} {lv:>2} {lb} [{_ansi(lt, ANSI['bold'], _tier_color(lt))}]"
        right = f"{_ansi(r_label, ANSI['bold'], ANSI['white'])} {rv:>2} {rb} [{_ansi(rt, ANSI['bold'], _tier_color(rt))}]"
        lines.append(_ansi_row(_pair(left, right, width), width, frame_color))

    return lines


def _equipment_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_section(lang, "equipment"), width - 2, ANSI["gold"]),
            width,
            frame_color,
        )
    ]
    slot_specs = [("main_slot", "main_hint", "◆"), ("aux_slot", "aux_hint", "◇"), ("sigil_slot", "sigil_hint", "✦")]
    show_hints = width >= 70
    for index, (slot_key, hint_key, glyph) in enumerate(slot_specs):
        slot_label = i18n.t_label(lang, slot_key)
        plugin_name = scan.plugin_names[index] if index < len(scan.plugin_names) else None
        if plugin_name:
            value = _ansi(plugin_name, ANSI["bold"], ANSI["white"])
            status = _ansi(f"[ {i18n.t_label(lang, 'bound')} ]", ANSI["bold"], ANSI["ice"])
        else:
            value = _ansi(i18n.t_label(lang, "empty_slot"), ANSI["dim"], ANSI["gray"])
            status = _ansi(f"[ {i18n.t_label(lang, 'empty')} ]", ANSI["dim"], ANSI["gray"])
        slot_text = f"{_ansi(f'{glyph} {slot_label} ', ANSI['bold'], ANSI['gold'])} {value}"
        if show_hints:
            hint = f"{status} {_ansi(i18n.t_label(lang, hint_key), ANSI['dim'], ANSI['gray'])}"
            lines.append(_ansi_row(_pair(slot_text, hint, width), width, frame_color))
        else:
            lines.append(_ansi_row(f"{slot_text}  {status}", width, frame_color))
    extra = max(0, len(scan.plugin_names) - len(slot_specs))
    if extra:
        overflow = ", ".join(scan.plugin_names[len(slot_specs) : len(slot_specs) + 4])
        lines.append(
            _ansi_row(
                _ansi(f"  + {extra} {i18n.t_label(lang, 'stowed')} // {overflow}", ANSI["dim"], ANSI["gray"]),
                width,
                frame_color,
            )
        )
    return lines


def _codex_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_section(lang, "disciplines"), width - 2, ANSI["ice"]),
            width,
            frame_color,
        )
    ]
    domains = ", ".join(profile.dominant_domains[:3]) if profile.dominant_domains else "—"
    lines.append(
        _ansi_row(
            _pair(
                f"{i18n.t_label(lang, 'techniques')} {_ansi(str(scan.skill_count), ANSI['bold'], ANSI['white'])} // "
                f"{i18n.t_label(lang, 'domains')} {_ansi(str(len(profile.dominant_domains)), ANSI['bold'], ANSI['white'])}",
                f"{i18n.t_label(lang, 'records')} {_ansi(str(scan.session_file_count), ANSI['bold'], ANSI['white'])} // "
                f"{i18n.t_label(lang, 'artifacts')} {_ansi(str(scan.plugin_count), ANSI['bold'], ANSI['white'])}",
                width,
            ),
            width,
            frame_color,
        )
    )
    for wrapped in _wrap_plain(f"{i18n.t_label(lang, 'dominant_domains')} // {domains}", width - 4):
        lines.append(_ansi_row(_ansi(f"· {wrapped}", ANSI["soft"]), width, frame_color))
    if scan.skill_categories:
        max_cat = max(scan.skill_categories.values())
        sorted_cats = sorted(scan.skill_categories.items(), key=lambda kv: (-kv[1], kv[0]))
        for category, count in sorted_cats[:6]:
            cat_bar = _ansi(
                _bar(count, max(max_cat, 1), width=12, filled="▰", empty="▱"),
                ANSI["bold"],
                ANSI["lavender"],
            )
            label = _pad_to(_ansi(category, ANSI["white"]), 22)
            count_text = _ansi(f"{count:>2}", ANSI["bold"], ANSI["white"])
            lines.append(_ansi_row(f"  {label}{cat_bar} {count_text}", width, frame_color))
    # Top skill names (Phase 1 display limit 8 — full list available in scan.top_skill_names)
    if scan.top_skill_names:
        lines.append(_ansi_row(_ansi(f"· {i18n.t_label(lang, 'techniques')}:", ANSI["dim"], ANSI["soft"]), width, frame_color))
        for name in scan.top_skill_names[:8]:
            lines.append(_ansi_row(_ansi(f"    {name}", ANSI["gray"]), width, frame_color))
    return lines


def _journal_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_label(lang, "recent_expeditions"), width - 2, ANSI["violet"]),
            width,
            frame_color,
        )
    ]
    # Phase 1 fallback: list recent session stems only (Phase 3 enriches from state.db).
    if scan.recent_sessions:
        for name in scan.recent_sessions[:10]:
            lines.append(_ansi_row(_ansi(f"· {name}", ANSI["soft"]), width, frame_color))
    else:
        lines.append(_ansi_row(_ansi("· (none)", ANSI["dim"], ANSI["gray"]), width, frame_color))
    return lines


def _chronicle_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_section(lang, "field_report"), width - 2, ANSI["violet"]),
            width,
            frame_color,
        )
    ]
    lines.append(
        _ansi_row(
            _pair(
                f"{i18n.t_label(lang, 'tool_traces')} {_ansi(str(scan.activity.session_tool_mentions), ANSI['bold'], ANSI['white'])}",
                f"{i18n.t_label(lang, 'hook_marks')} {_ansi(str(scan.activity.plugin_hook_mentions), ANSI['bold'], ANSI['white'])}",
                width,
            ),
            width,
            frame_color,
        )
    )
    lines.append(
        _ansi_row(
            _pair(
                f"{i18n.t_label(lang, 'codex_depth')} {_ansi(str(scan.activity.skill_words), ANSI['bold'], ANSI['white'])}",
                f"{i18n.t_label(lang, 'memory_strands')} {_ansi(str(scan.activity.memory_lines), ANSI['bold'], ANSI['white'])}",
                width,
            ),
            width,
            frame_color,
        )
    )
    lines.append(
        _ansi_row(
            _pair(
                f"{i18n.t_label(lang, 'memories')} {_ansi(str(scan.memory_entries), ANSI['bold'], ANSI['white'])} // "
                f"{i18n.t_label(lang, 'user_bonds')} {_ansi(str(scan.user_entries), ANSI['bold'], ANSI['white'])}",
                f"{i18n.t_label(lang, 'echoes')} {_ansi(str(scan.log_file_count), ANSI['bold'], ANSI['white'])}",
                width,
            ),
            width,
            frame_color,
        )
    )
    return lines


def _rituals_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_label(lang, "rituals"), width - 2, ANSI["mint"]),
            width,
            frame_color,
        )
    ]
    lines.append(
        _ansi_row(
            _pair(
                f"{i18n.t_label(lang, 'rituals')} {_ansi(str(scan.cron_file_count), ANSI['bold'], ANSI['white'])}",
                f"{i18n.t_label(lang, 'ritual_glyphs')} {_ansi(str(scan.activity.cron_schedule_mentions), ANSI['bold'], ANSI['white'])}",
                width,
            ),
            width,
            frame_color,
        )
    )
    return lines


def _effects_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_section(lang, "active_buffs"), width - 2, ANSI["violet"]),
            width,
            frame_color,
        )
    ]
    if profile.buff_ids:
        for buff_id in profile.buff_ids:
            buff = i18n.t_buff(lang, buff_id)
            glyph = "✗" if buff_id == "wounded" else "✦"
            glyph_color = ANSI["red"] if buff_id == "wounded" else ANSI["gold"]
            mod_color = ANSI["red"] if buff["modifier"].startswith("-") else ANSI["ice"]
            name_pad = 18 if width >= 70 else 14
            row = (
                f"{_ansi(glyph, ANSI['bold'], glyph_color)} "
                f"{_pad_to(_ansi(buff['name'], ANSI['bold'], ANSI['white']), name_pad)} "
                f"{_ansi(buff['modifier'], ANSI['bold'], mod_color)}"
            )
            if width >= 70:
                row += f"  {_ansi('‧ ' + buff['hint'], ANSI['dim'], ANSI['gray'])}"
            lines.append(_ansi_row(row, width, frame_color))
    else:
        lines.append(
            _ansi_row(_ansi(f"· {i18n.t_label(lang, 'no_buffs')}", ANSI["dim"], ANSI["gray"]), width, frame_color)
        )

    lines.append(_ansi_row("", width, frame_color))
    lines.append(
        _ansi_row(_ansi_section(i18n.t_section(lang, "achievements"), width - 2, ANSI["gold"]), width, frame_color)
    )
    if profile.achievements:
        for achievement in profile.achievements[:8]:
            lines.append(
                _ansi_row(f"{_ansi('◆', ANSI['gold'], ANSI['bold'])} {achievement}", width, frame_color)
            )
    else:
        lines.append(
            _ansi_row(_ansi(i18n.t_label(lang, "no_achievements"), ANSI["dim"], ANSI["gray"]), width, frame_color)
        )
    return lines


def _diagnostics_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    scar_color = ANSI["red"] if scan.activity.session_error_mentions else ANSI["gray"]
    lines: list[str] = [
        _ansi_row(
            _ansi_section(i18n.t_label(lang, "error_scars"), width - 2, ANSI["red"]),
            width,
            frame_color,
        )
    ]
    lines.append(
        _ansi_row(
            _pair(
                f"{i18n.t_label(lang, 'error_scars')} {_ansi(str(scan.activity.session_error_mentions), ANSI['bold'], scar_color)}",
                f"{i18n.t_label(lang, 'records')} {_ansi(str(scan.session_file_count), ANSI['bold'], ANSI['white'])}",
                width,
            ),
            width,
            frame_color,
        )
    )
    return lines


def _realm_rows(profile: CharacterProfile, width: int, lang: str) -> list[str]:
    frame_color = _frame_color()
    scan = profile.scan
    home_path = scan.hermes_home
    home_label = home_path.rstrip("/").split("/")[-1] or home_path
    lines: list[str] = [
        _ansi_row(_ansi_section(i18n.t_section(lang, "realm"), width - 2, ANSI["soft"]), width, frame_color),
        _ansi_row(
            _pair(
                f"{_ansi('◷ ' + i18n.t_label(lang, 'realm_word'), ANSI['dim'], ANSI['soft'])}  "
                f"{_ansi(home_label, ANSI['bold'], ANSI['white'])}",
                f"{_ansi('◊ ' + i18n.t_label(lang, 'profiles_word'), ANSI['dim'], ANSI['soft'])}  "
                f"{_ansi(str(scan.profile_count), ANSI['bold'], ANSI['white'])} {i18n.t_label(lang, 'bound_word')}",
                width,
            ),
            width,
            frame_color,
        ),
    ]
    for wrapped in _wrap_plain(f"{i18n.t_label(lang, 'path_word')} // {home_path}", width - 4):
        lines.append(_ansi_row(_ansi(f"  {wrapped}", ANSI["dim"], ANSI["gray"]), width, frame_color))
    # Profile summary appended as part of Status/Realm overview.
    lines.append(_ansi_row("", width, frame_color))
    lines.append(_ansi_row(_ansi_section(i18n.t_section(lang, "profile"), width - 2, ANSI["soft"]), width, frame_color))
    for wrapped in _wrap_plain(profile.summary, width - 2):
        lines.append(_ansi_row(_ansi(wrapped, ANSI["gray"]), width, frame_color))
    return lines


def _resolve_tab_width(width: int | None) -> int:
    return width or 78


def render_status_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001  -- Phase 3 populates
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    mode = _resolve_banner_mode(width, "auto")
    rows = _status_rows(profile, width, lang, mode)
    rows.append(_ansi_row("", width, _frame_color()))
    rows.extend(_realm_rows(profile, width, lang))
    return "\n".join(rows)


def render_equipment_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_equipment_rows(profile, width, lang))


def render_codex_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_codex_rows(profile, width, lang))


def render_journal_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_journal_rows(profile, width, lang))


def render_chronicle_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_chronicle_rows(profile, width, lang))


def render_rituals_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_rituals_rows(profile, width, lang))


def render_effects_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_effects_rows(profile, width, lang))


def render_diagnostics_tab(
    profile: CharacterProfile,
    *,
    width: int | None = None,
    lang: str | None = None,
    telemetry: object | None = None,  # noqa: ARG001
) -> str:
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(lang or profile.lang)
    return "\n".join(_diagnostics_rows(profile, width, lang))


_TAB_RENDERERS = {
    "status": render_status_tab,
    "equipment": render_equipment_tab,
    "codex": render_codex_tab,
    "journal": render_journal_tab,
    "chronicle": render_chronicle_tab,
    "rituals": render_rituals_tab,
    "effects": render_effects_tab,
    "diagnostics": render_diagnostics_tab,
}


def render_tab(tab_id: str, profile: CharacterProfile, **kwargs) -> str:
    """Dispatch helper — returns a tab's rendered string by id."""
    try:
        fn = _TAB_RENDERERS[tab_id]
    except KeyError as err:  # pragma: no cover - defensive
        raise ValueError(f"Unknown tab id: {tab_id!r}. Known: {list(_TAB_RENDERERS)}") from err
    return fn(profile, **kwargs)


def render_static_tabs_panel(
    profile: CharacterProfile,
    banner_mode: str = "auto",
    width: int | None = None,
    telemetry: object | None = None,
) -> str:
    """Render all 8 tabs concatenated for ``--format tabs`` static export.

    Note: this is a NEW output format; it does NOT replace ``render_ansi_panel``
    which remains the ``--format ansi`` single-panel output (parity-tested).
    """
    width = _resolve_tab_width(width)
    lang = i18n.normalize_lang(profile.lang)
    mode = _resolve_banner_mode(width, banner_mode)
    frame_color = _frame_color()

    lines: list[str] = []
    lines.extend(_system_window_banner(width, lang, mode))
    lines.append("")

    for tab_id in TAB_IDS:
        title = i18n.t_label(lang, f"tab_{tab_id}")
        divider = _ansi_section(title, width - 2, ANSI["lavender"])
        lines.append(_ansi_row(divider, width, frame_color))
        lines.append(render_tab(tab_id, profile, width=width, lang=lang, telemetry=telemetry))
        lines.append(_ansi_row("", width, frame_color))

    lines.append(_ansi(f"╰{'─' * (width + 2)}╯", ANSI["bold"], ANSI["deep_violet"]))
    return "\n".join(lines)
