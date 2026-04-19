from __future__ import annotations

from . import i18n
from .models import (
    CharacterProfile,
    Equipment,
    ScanSummary,
    StatBlock,
    TelemetrySnapshot,
)


RANK_TIERS: list[tuple[int, str]] = [
    (1, "bronze"),
    (8, "silver"),
    (16, "gold"),
    (25, "mythic"),
]


def _rank_id_for_level(level: int) -> str:
    rank = "bronze"
    for minimum, label in RANK_TIERS:
        if level >= minimum:
            rank = label
    return rank


def _dominant_domains(scan: ScanSummary) -> list[str]:
    pairs = sorted(scan.skill_categories.items(), key=lambda item: (-item[1], item[0]))
    return [name for name, _ in pairs[:3]]


def _suffix_index(scan: ScanSummary) -> int:
    if scan.skill_count >= 30 or scan.session_file_count >= 100 or scan.activity.session_tool_mentions >= 100:
        return 2
    if scan.memory_entries + scan.user_entries >= 10 or scan.plugin_count >= 2 or scan.activity.plugin_hook_mentions >= 3:
        return 1
    return 0


def _primary_class_id(scan: ScanSummary) -> str:
    domains = _dominant_domains(scan)
    if (scan.plugin_count >= 2 or scan.activity.plugin_hook_mentions >= 2) and scan.skill_count >= 12:
        return "shadow_commander"
    if scan.memory_entries + scan.user_entries >= 12 and scan.skill_count >= 8:
        return "memory_weaver"
    if scan.activity.cron_schedule_mentions >= 4 and scan.cron_file_count >= 1:
        return "ops_summoner"
    for domain in domains:
        if domain in i18n.CLASS_DOMAIN_RULES:
            return i18n.CLASS_DOMAIN_RULES[domain]
    if len(scan.skill_categories) >= 4 and scan.skill_count >= 10:
        return "adaptive_agent"
    if scan.memory_entries + scan.user_entries >= 8:
        return "memory_weaver"
    return "hunter_candidate"


def _threat_id(scan: ScanSummary, dominant_domain_count: int) -> str:
    score = (
        dominant_domain_count
        + min(scan.plugin_count, 3)
        + min(scan.cron_file_count, 3)
        + min(scan.session_file_count // 25, 4)
        + min(scan.activity.session_tool_mentions // 40, 3)
    )
    if score >= 10:
        return "archive_anomaly"
    if score >= 7:
        return "system_ascendant"
    if score >= 4:
        return "field_ready"
    return "candidate_presence"


def _awakening_id(level: int) -> str:
    if level >= 40:
        return "system_overclock"
    if level >= 25:
        return "shadow_awakening"
    if level >= 14:
        return "hunter_ascension"
    if level >= 7:
        return "class_emergence"
    return "candidate_phase"


def _build_achievement_ids(scan: ScanSummary, primary_class_id: str, rank_id: str) -> list[str]:
    ids: list[str] = []
    total_memory = scan.memory_entries + scan.user_entries
    if total_memory > 0:
        ids.append("memory_spark")
    if total_memory >= 10:
        ids.append("lorekeeper")
    if scan.skill_count >= 5:
        ids.append("skill_archivist")
    if scan.skill_count >= 20:
        ids.append("skill_tree_unlocked")
    if scan.activity.skill_words >= 5000:
        ids.append("codex_devourer")
    if scan.plugin_count >= 1:
        ids.append("artifact_binder")
    if scan.plugin_count >= 3:
        ids.append("extension_architect")
    if scan.activity.plugin_hook_mentions >= 3:
        ids.append("hook_whisperer")
    if scan.profile_count >= 1:
        ids.append("profile_wanderer")
    if scan.profile_count >= 3:
        ids.append("multiform_traveler")
    if scan.cron_file_count >= 1:
        ids.append("ritual_keeper")
    if scan.activity.cron_schedule_mentions >= 3:
        ids.append("clock_sigil")
    if scan.session_file_count >= 25:
        ids.append("battle_tested_operator")
    if scan.session_file_count >= 100:
        ids.append("dungeon_clear_veteran")
    if scan.activity.session_tool_mentions >= 75:
        ids.append("toolchain_berserker")
    if len(scan.skill_categories) >= 4:
        ids.append("cross_discipline_raider")
    if scan.log_file_count >= 10:
        ids.append("echoes_in_logsea")
    if scan.activity.session_error_mentions >= 10:
        ids.append("bug_survivor")
    if primary_class_id == "toolsmith" and scan.skill_count >= 8:
        ids.append("forged_in_tools")
    if primary_class_id == "memory_weaver" and total_memory >= 12:
        ids.append("threadbinder_recall")
    if primary_class_id == "shadow_commander" and scan.plugin_count >= 2:
        ids.append("commander_of_echoes")
    if rank_id == "mythic":
        ids.append("system_overlord")
    return ids


def _build_buff_ids(scan: ScanSummary) -> list[str]:
    activity = scan.activity
    ids: list[str] = []
    if activity.memory_lines >= 5:
        ids.append("memory_resonance")
    if activity.skill_words >= 500:
        ids.append("codex_mastery")
    if activity.plugin_hook_mentions >= 2:
        ids.append("hook_symbiosis")
    if activity.cron_schedule_mentions >= 2:
        ids.append("ritual_bond")
    if activity.session_tool_mentions >= 50:
        ids.append("battle_hardened")
    if len(scan.skill_categories) >= 3:
        ids.append("cross_discipline")
    if scan.profile_count >= 2:
        ids.append("multiform_echo")
    if activity.session_error_mentions >= 5:
        ids.append("wounded")
    return ids[:6]


def _compute_total_exp(scan: ScanSummary) -> int:
    return (
        scan.memory_entries * 6
        + scan.user_entries * 8
        + scan.skill_count * 12
        + scan.profile_count * 20
        + min(scan.session_file_count, 300) * 2
        + min(scan.activity.session_tool_mentions, 300)
        + scan.plugin_count * 15
        + min(scan.activity.plugin_hook_mentions, 80) * 5
        + min(scan.log_file_count, 120)
        + scan.cron_file_count * 8
        + min(scan.activity.cron_schedule_mentions, 80) * 3
        + len(scan.skill_categories) * 18
        + min(scan.activity.skill_words // 100, 150)
        + min(scan.activity.memory_lines * 2, 100)
        - min(scan.activity.session_error_mentions, 60)
    )


def _compute_stats(scan: ScanSummary, total_exp: int) -> StatBlock:
    level = max(1, total_exp // 50 + 1)
    exp_into_level = total_exp % 50
    domain_variety = len(scan.skill_categories)
    total_memory = scan.memory_entries + scan.user_entries
    intelligence = min(20, 5 + scan.skill_count + domain_variety + min(scan.activity.skill_words // 1500, 3))
    wisdom = min(20, 4 + total_memory + min(scan.activity.memory_lines // 10, 4))
    strength = min(20, 4 + scan.plugin_count + scan.cron_file_count + scan.profile_count + min(scan.activity.plugin_hook_mentions // 2, 4))
    agility = min(20, 4 + domain_variety + min(scan.session_file_count // 10, 10) + min(scan.activity.session_tool_mentions // 25, 3))
    charisma = min(20, 4 + min(scan.user_entries, 8) + min(scan.profile_count, 4) + min(scan.plugin_count, 4) + min(scan.activity.plugin_manifest_count, 2))
    luck = min(20, 3 + max(1, domain_variety // 2) + min(scan.plugin_count, 3) + (1 if scan.cron_file_count else 0) + (1 if scan.activity.session_error_mentions else 0))
    return StatBlock(
        level=level,
        exp_into_level=exp_into_level,
        exp_to_next_level=50,
        total_exp=total_exp,
        strength=strength,
        intelligence=intelligence,
        wisdom=wisdom,
        agility=agility,
        charisma=charisma,
        luck=luck,
    )


def _clamp_stat(value: float) -> int:
    """Clamp a computed stat to the 0..20 attribute range (rounded)."""
    return max(0, min(20, round(value)))


def _compute_telemetry_attributes(
    telemetry: TelemetrySnapshot,
) -> dict[str, int]:
    """Compute the 6 Phase-2 attributes from telemetry (plan W2.5).

    Each attribute is clamped to the [0, 20] range the renderer expects.
    """
    sessions = telemetry.recent_sessions
    session_count = max(len(sessions), 1)

    # ENDURANCE — average session duration in minutes (longer runs → higher).
    durations = [s.duration_seconds or 0.0 for s in sessions]
    avg_minutes = (sum(durations) / session_count) / 60.0 if durations else 0.0
    endurance = _clamp_stat(4 + avg_minutes / 15.0)

    # PRECISION — inverse incomplete-session rate. Only ``ended_at IS NULL``
    # flags an incomplete run; compression is a normal split (Appendix B)
    # and is already surfaced in the Overheat vital, so it must NOT
    # double-count here.
    partials = sum(1 for s in sessions if s.ended_at is None)
    error_rate = partials / session_count
    precision = _clamp_stat(20 * (1.0 - error_rate))

    # RESONANCE — lifetime cache hit rate (cache_read / (cache_read + input)).
    resonance = _clamp_stat(20 * telemetry.lifetime_tokens.cache_hit_rate)

    # CLARITY — reasoning-token ratio (depth of thought per output).
    tokens = telemetry.lifetime_tokens
    reasoning_ratio = (
        tokens.reasoning_tokens / tokens.output_tokens if tokens.output_tokens else 0.0
    )
    clarity = _clamp_stat(20 * reasoning_ratio)

    # REACH — model diversity proxy (lacking per-model context-window data in
    # state.db v6). 3 distinct models ⇒ 9 points; clamp at 20.
    reach = _clamp_stat(3 * len(telemetry.model_usage))

    # TEMPO — average tool-calls-per-minute across sessions.
    def _tcpm(s) -> float:
        dur_min = (s.duration_seconds or 0.0) / 60.0
        return s.tool_call_count / dur_min if dur_min > 0 else 0.0

    tempos = [_tcpm(s) for s in sessions if (s.duration_seconds or 0) > 0]
    avg_tempo = sum(tempos) / len(tempos) if tempos else 0.0
    tempo = _clamp_stat(4 * avg_tempo)

    return {
        "endurance": endurance,
        "precision": precision,
        "resonance": resonance,
        "clarity": clarity,
        "reach": reach,
        "tempo": tempo,
    }


def _build_equipment(telemetry: TelemetrySnapshot | None, scan: ScanSummary) -> Equipment:
    """Correct Equipment mapping (plan W2.6) — replaces plugin_names[:3] hack."""
    main_weapon: str | None = None
    hotbar: list = []
    if telemetry is not None:
        if telemetry.recent_sessions:
            main_weapon = telemetry.recent_sessions[0].model
        hotbar = list(telemetry.top_tools[:5])
    return Equipment(
        main_weapon=main_weapon,
        armor_slots=list(scan.plugin_names),
        trinkets=list(scan.toolset_names),
        hotbar=hotbar,
    )


def build_character_profile(
    scan: ScanSummary,
    name: str = "Hermes",
    lang: str = "en",
    telemetry: TelemetrySnapshot | None = None,
    fallback_reason: str | None = None,
) -> CharacterProfile:
    lang = i18n.normalize_lang(lang)
    total_exp = _compute_total_exp(scan)
    stats = _compute_stats(scan, total_exp)
    rank_id = _rank_id_for_level(stats.level)
    primary_class_id = _primary_class_id(scan)
    suffix_index = _suffix_index(scan)
    title = i18n.title_for(lang, primary_class_id, rank_id, suffix_index)
    domains = _dominant_domains(scan)
    achievement_ids = _build_achievement_ids(scan, primary_class_id, rank_id)
    achievements = [i18n.t_achievement(lang, aid) for aid in achievement_ids]
    buff_ids = _build_buff_ids(scan)
    threat_id = _threat_id(scan, len(domains))
    awakening_id = _awakening_id(stats.level)

    # Phase 2: populate the 6 new attributes when telemetry is available;
    # leave as None (StatBlock default) when falling back to the file scanner
    # so the renderer can show a "data unavailable" hint.
    if telemetry is not None:
        extras = _compute_telemetry_attributes(telemetry)
        stats = StatBlock(
            level=stats.level,
            exp_into_level=stats.exp_into_level,
            exp_to_next_level=stats.exp_to_next_level,
            total_exp=stats.total_exp,
            strength=stats.strength,
            intelligence=stats.intelligence,
            wisdom=stats.wisdom,
            agility=stats.agility,
            charisma=stats.charisma,
            luck=stats.luck,
            endurance=extras["endurance"],
            precision=extras["precision"],
            resonance=extras["resonance"],
            clarity=extras["clarity"],
            reach=extras["reach"],
            tempo=extras["tempo"],
        )

    equipment = _build_equipment(telemetry, scan)

    class_info = i18n.t_class(lang, primary_class_id)
    primary_class_name = class_info["name"]
    flavor = class_info["flavor"]

    home_str = str(scan.hermes_home)
    home_label = home_str.rstrip("/").split("/")[-1] or home_str
    summary = i18n.narrative(
        lang,
        home_label=home_label,
        primary_class_name=primary_class_name,
        flavor=flavor,
        skill_count=scan.skill_count,
        domain_count=len(scan.skill_categories),
        tool_mentions=scan.activity.session_tool_mentions,
    )

    return CharacterProfile(
        name=name,
        title=title,
        primary_class=primary_class_name,
        rank=i18n.t_rank(lang, rank_id),
        summary=summary,
        stats=stats,
        scan=scan,
        achievements=achievements,
        dominant_domains=domains,
        lang=lang,
        primary_class_id=primary_class_id,
        rank_id=rank_id,
        achievement_ids=achievement_ids,
        buff_ids=buff_ids,
        threat_id=threat_id,
        awakening_id=awakening_id,
        telemetry=telemetry,
        equipment=equipment,
        fallback_reason=fallback_reason,
    )
