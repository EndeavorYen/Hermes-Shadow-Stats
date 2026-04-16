from __future__ import annotations

from . import i18n
from .models import CharacterProfile, ScanSummary, StatBlock


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


def build_character_profile(scan: ScanSummary, name: str = "Hermes", lang: str = "en") -> CharacterProfile:
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
    )
