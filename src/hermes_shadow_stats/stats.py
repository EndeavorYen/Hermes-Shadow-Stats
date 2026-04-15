from __future__ import annotations

from .models import CharacterProfile, ScanSummary, StatBlock


CLASS_RULES = {
    "software-development": "Toolsmith",
    "github": "Code Alchemist",
    "devops": "Ops Summoner",
    "research": "Research Ranger",
    "note-taking": "Memory Weaver",
    "productivity": "Workflow Scribe",
    "mlops": "Model Hunter",
    "autonomous-ai-agents": "Shadow Commander",
    "creative": "Rune Artisan",
    "social-media": "Signal Duelist",
    "mcp": "Protocol Walker",
}

RANK_TIERS = [
    (1, "Bronze"),
    (8, "Silver"),
    (16, "Gold"),
    (25, "Mythic"),
]

TITLE_PATHS = {
    "Bronze": ["Initiate", "Awakened", "Field Scout"],
    "Silver": ["Adept", "Pathfinder", "Dungeon Breaker"],
    "Gold": ["Ascendant", "Elite Raider", "System Tactician"],
    "Mythic": ["Shadow Monarch", "Worldline Breaker", "Archive Sovereign"],
}

FLAVOR_TAGS = {
    "Toolsmith": "forges reliable solutions from raw tools",
    "Code Alchemist": "transmutes repositories into working systems",
    "Ops Summoner": "binds infrastructure, jobs, and daemon-like rituals",
    "Research Ranger": "hunts signal across scattered knowledge fields",
    "Memory Weaver": "turns fragmented context into durable insight",
    "Workflow Scribe": "converts friction into repeatable rituals",
    "Model Hunter": "tracks models, benchmarks, and inference beasts",
    "Shadow Commander": "coordinates specialist agents as an army of echoes",
    "Rune Artisan": "shapes style, symbols, and creative output into artifacts",
    "Signal Duelist": "navigates public channels and attention battlegrounds",
    "Protocol Walker": "moves between systems through tool and protocol gates",
    "Adaptive Agent": "keeps evolving without committing to a single path",
    "Hunter Candidate": "has sensed the system, but not mastered it yet",
}


def _indefinite_article(text: str) -> str:
    stripped = (text or "").strip().lower()
    if not stripped:
        return "a"
    return "an" if stripped[0] in "aeiou" else "a"


def _rank_for_level(level: int) -> str:
    rank = "Bronze"
    for minimum, label in RANK_TIERS:
        if level >= minimum:
            rank = label
    return rank


def _dominant_domains(scan: ScanSummary) -> list[str]:
    pairs = sorted(scan.skill_categories.items(), key=lambda item: (-item[1], item[0]))
    return [name for name, _ in pairs[:3]]


def _pick_title(rank: str, scan: ScanSummary, primary_class: str) -> str:
    options = TITLE_PATHS[rank]
    if scan.skill_count >= 30 or scan.session_file_count >= 100 or scan.activity.session_tool_mentions >= 100:
        suffix = options[2]
    elif scan.memory_entries + scan.user_entries >= 10 or scan.plugin_count >= 2 or scan.activity.plugin_hook_mentions >= 3:
        suffix = options[1]
    else:
        suffix = options[0]

    if primary_class == "Memory Weaver" and rank == "Mythic":
        suffix = "Archive Sovereign"
    elif primary_class == "Shadow Commander" and rank in {"Gold", "Mythic"}:
        suffix = "System Tactician"
    elif primary_class == "Research Ranger" and rank in {"Silver", "Gold"}:
        suffix = "Pathfinder"
    elif primary_class == "Model Hunter" and rank == "Mythic":
        suffix = "Archive Sovereign"

    return f"{primary_class} {suffix}"


def _primary_class(scan: ScanSummary) -> str:
    domains = _dominant_domains(scan)

    if (scan.plugin_count >= 2 or scan.activity.plugin_hook_mentions >= 2) and scan.skill_count >= 12:
        return "Shadow Commander"
    if scan.memory_entries + scan.user_entries >= 12 and scan.skill_count >= 8:
        return "Memory Weaver"
    if scan.activity.cron_schedule_mentions >= 4 and scan.cron_file_count >= 1:
        return "Ops Summoner"

    for domain in domains:
        if domain in CLASS_RULES:
            return CLASS_RULES[domain]

    if len(scan.skill_categories) >= 4 and scan.skill_count >= 10:
        return "Adaptive Agent"
    if scan.memory_entries + scan.user_entries >= 8:
        return "Memory Weaver"
    return "Hunter Candidate"


def _build_achievements(scan: ScanSummary, primary_class: str, rank: str) -> list[str]:
    achievements: list[str] = []
    total_memory = scan.memory_entries + scan.user_entries

    if total_memory > 0:
        achievements.append("First Persistent Memory")
    if total_memory >= 10:
        achievements.append("Lorekeeper")
    if scan.skill_count >= 5:
        achievements.append("Skill Archivist")
    if scan.skill_count >= 20:
        achievements.append("Skill Tree Unlocked")
    if scan.activity.skill_words >= 5000:
        achievements.append("Codex Devourer")
    if scan.plugin_count >= 1:
        achievements.append("Plugin Tinkerer")
    if scan.plugin_count >= 3:
        achievements.append("Extension Architect")
    if scan.activity.plugin_hook_mentions >= 3:
        achievements.append("Hook Whisperer")
    if scan.profile_count >= 1:
        achievements.append("Profile Wanderer")
    if scan.profile_count >= 3:
        achievements.append("Multiform Traveler")
    if scan.cron_file_count >= 1:
        achievements.append("Cron Tamer")
    if scan.activity.cron_schedule_mentions >= 3:
        achievements.append("Scheduler Pact")
    if scan.session_file_count >= 25:
        achievements.append("Battle-Tested Operator")
    if scan.session_file_count >= 100:
        achievements.append("Dungeon Clear Veteran")
    if scan.activity.session_tool_mentions >= 75:
        achievements.append("Toolchain Berserker")
    if len(scan.skill_categories) >= 4:
        achievements.append("Cross-Discipline Raider")
    if scan.log_file_count >= 10:
        achievements.append("Echoes in the Logsea")
    if scan.activity.session_error_mentions >= 10:
        achievements.append("Bug Survivor")
    if primary_class == "Toolsmith" and scan.skill_count >= 8:
        achievements.append("Forged in Tools")
    if primary_class == "Memory Weaver" and total_memory >= 12:
        achievements.append("Threadbinder of Recall")
    if primary_class == "Shadow Commander" and scan.plugin_count >= 2:
        achievements.append("Commander of Echoes")
    if rank == "Mythic":
        achievements.append("System Overlord")
    return achievements


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
    exp_to_next_level = 50

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
        exp_to_next_level=exp_to_next_level,
        total_exp=total_exp,
        strength=strength,
        intelligence=intelligence,
        wisdom=wisdom,
        agility=agility,
        charisma=charisma,
        luck=luck,
    )


def build_character_profile(scan: ScanSummary, name: str = "Hermes") -> CharacterProfile:
    total_exp = _compute_total_exp(scan)
    stats = _compute_stats(scan, total_exp)
    rank = _rank_for_level(stats.level)
    primary_class = _primary_class(scan)
    title = _pick_title(rank, scan, primary_class)
    domains = _dominant_domains(scan)
    achievements = _build_achievements(scan, primary_class, rank)
    flavor = FLAVOR_TAGS.get(primary_class, FLAVOR_TAGS["Adaptive Agent"])

    home_str = str(scan.hermes_home)
    home_label = home_str.rstrip("/").split("/")[-1] or home_str
    article = _indefinite_article(primary_class)
    summary = (
        f"A read-only shadow profile reconstructed from the {home_label} archive. "
        f"This entity currently manifests as {article} {primary_class.lower()} and {flavor}. "
        f"It has learned {scan.skill_count} persistent skill(s) across {len(scan.skill_categories)} domain(s), "
        f"with {scan.activity.session_tool_mentions} observed tool-signatures in archived session traces."
    )

    return CharacterProfile(
        name=name,
        title=title,
        primary_class=primary_class,
        rank=rank,
        summary=summary,
        stats=stats,
        scan=scan,
        achievements=achievements,
        dominant_domains=domains,
    )
